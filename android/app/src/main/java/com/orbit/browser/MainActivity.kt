package com.orbit.browser

import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.webkit.CookieManager
import android.webkit.DownloadListener
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceError
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.PopupWindow
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    private val api = "https://orbit-api-9uqa.onrender.com"
    private val appVersion = "1.12"
    private val orbitBg = Color.rgb(5, 7, 18)
    private val orbitSurface = Color.rgb(11, 16, 35)
    private val orbitSurface2 = Color.rgb(19, 26, 53)
    private val orbitBorder = Color.rgb(48, 66, 125)
    private val orbitAccent = Color.rgb(118, 108, 255)
    private val orbitAccent2 = Color.rgb(81, 211, 255)
    private val orbitTextColor = Color.rgb(245, 247, 255)
    private val orbitMuted = Color.rgb(153, 165, 199)
    private var interfaceVariant: String = "BASE"


    private lateinit var root: LinearLayout
    private lateinit var content: FrameLayout
    private lateinit var address: EditText
    private lateinit var pageTitle: TextView
    private lateinit var bottomNav: LinearLayout

    private val tabs = mutableListOf<WebView>()
    private var current = -1
    private val prefs by lazy { getSharedPreferences("orbit", Context.MODE_PRIVATE) }
    private val executor = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())
    private var user: JSONObject? = null
    private var token: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        token = prefs.getString("token", null)
        loadStoredProfile()
        interfaceVariant = prefs.getString("interface_variant", "BASE") ?: "BASE"
        buildUi()
        showWelcome()
        addTab("file:///android_asset/orbit_home.html")
        handler.postDelayed({ sync(false) }, 1800)
        handler.postDelayed(object : Runnable {
            override fun run() {
                sync(false)
                handler.postDelayed(this, 60000)
            }
        }, 30000)
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                val view = currentWeb()
                if (view != null && view.canGoBack()) view.goBack() else showHome()
            }
        })
    }

    private fun loadStoredProfile() {
        val raw = prefs.getString("profile", null)
        if (!raw.isNullOrBlank()) {
            user = runCatching { JSONObject(raw) }.getOrNull()
        }
    }

    private fun buildUi() {
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(orbitBg)
        }
        setContentView(root)

        val top = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(12, 8, 12, 6)
            setBackgroundColor(orbitSurface)
        }

        applyInterfaceVariant(top)

        val brand = TextView(this).apply {
            text = "✦  ORBIT"
            setTextColor(orbitTextColor)
            textSize = 19f
            gravity = Gravity.CENTER_VERTICAL
            setTypeface(typeface, Typeface.BOLD)
        }
        top.addView(brand, LinearLayout.LayoutParams(-1, 38))

        val bar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        bar.addView(topButton("‹") { currentWeb()?.goBack() }, LinearLayout.LayoutParams(42, 46))
        bar.addView(topButton("›") { currentWeb()?.goForward() }, LinearLayout.LayoutParams(42, 46))
        bar.addView(topButton("↻") { currentWeb()?.reload() }, LinearLayout.LayoutParams(42, 46))

        address = EditText(this).apply {
            hint = "Поиск в Orbit или адрес"
            setHintTextColor(orbitMuted)
            setTextColor(orbitTextColor)
            textSize = 15f
            setSingleLine(true)
            setPadding(16, 0, 16, 0)
            setBackgroundColor(orbitSurface2)
            setOnEditorActionListener { _, _, _ -> navigate(); true }
        }
        bar.addView(address, LinearLayout.LayoutParams(0, 46, 1f))
        bar.addView(topButton("●") { showProfile() }, LinearLayout.LayoutParams(42, 46))
        top.addView(bar)

        pageTitle = TextView(this).apply { visibility = View.GONE }
        root.addView(top)

        content = FrameLayout(this)
        root.addView(content, LinearLayout.LayoutParams(-1, 0, 1f))

        bottomNav = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
            setBackgroundColor(orbitSurface)
            setPadding(4, 4, 4, 6)
        }
        val items = listOf(
            "⌂" to { showHome() },
            "☆" to { showSimple("bookmarks") },
            "◷" to { showSimple("history") },
            "↓" to { showSimple("downloads") },
            "●" to { showProfile() }
        )
        items.forEach { (label, action) ->
            bottomNav.addView(navItem(label, action), LinearLayout.LayoutParams(0, 54, 1f))
        }
        root.addView(bottomNav)
    }

    private fun applyInterfaceVariant(top: ViewGroup) {
        when (interfaceVariant) {
            "GOOGLE" -> {
                top.setPadding(10, 6, 10, 4)
                top.setBackgroundColor(Color.rgb(248, 249, 250))
            }
            "MINIMAL" -> {
                top.setPadding(8, 4, 8, 2)
            }
            "COMPACT" -> {
                top.setPadding(8, 2, 8, 2)
            }
            "GLASS" -> {
                top.alpha = 0.96f
            }
            else -> Unit
        }
    }

    private fun setInterfaceVariant(value: String) {
        interfaceVariant = value
        prefs.edit().putString("interface_variant", value).apply()
        notifyUser("Интерфейс изменён", variantLabel(value))
        buildUi()
        showBrowser()
    }

    private fun variantLabel(value: String): String = when (value) {
        "GOOGLE" -> "Как Google"
        "MINIMAL" -> "Минимализм"
        "COMPACT" -> "Компактный"
        "GLASS" -> "Стекло"
        else -> "Базовый"
    }

    private fun topButton(label: String, action: () -> Unit): TextView = TextView(this).apply {
        text = label
        textSize = 20f
        gravity = Gravity.CENTER
        setTextColor(orbitTextColor)
        setOnClickListener { action() }
    }

    private fun navItem(label: String, action: () -> Unit): TextView = TextView(this).apply {
        text = label
        textSize = 21f
        gravity = Gravity.CENTER
        setTextColor(orbitMuted)
        setOnClickListener { action() }
    }

    private fun showWelcome() {
        val overlay = FrameLayout(this).apply { setBackgroundColor(orbitBg); elevation = 100f }
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; gravity = Gravity.CENTER }
        val welcome = TextView(this).apply {
            text = "WELCOM"
            textSize = 46f
            setTextColor(orbitTextColor)
            gravity = Gravity.CENTER
            typeface = Typeface.create("sans-serif", Typeface.BOLD)
        }
        val sub = TextView(this).apply {
            text = "ORBIT BROWSER"
            textSize = 11f
            setTextColor(orbitAccent)
            gravity = Gravity.CENTER
            letterSpacing = .25f
        }
        box.addView(welcome)
        box.addView(sub)
        overlay.addView(box, FrameLayout.LayoutParams(-1, -1))
        content.addView(overlay, FrameLayout.LayoutParams(-1, -1))
        welcome.alpha = 0f
        sub.alpha = 0f
        welcome.animate().alpha(1f).setDuration(350).withEndAction {
            sub.animate().alpha(1f).setDuration(250).withEndAction {
                overlay.animate().alpha(0f).setDuration(350).withEndAction { content.removeView(overlay) }
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configure(view: WebView) {
        view.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = false
            cacheMode = WebSettings.LOAD_DEFAULT
            loadsImagesAutomatically = true
            blockNetworkLoads = false
            mediaPlaybackRequiresUserGesture = true
            builtInZoomControls = false
            displayZoomControls = false
            setSupportZoom(true)
            setSupportMultipleWindows(false)
            setMediaPlaybackRequiresUserGesture(true)
            javaScriptCanOpenWindowsAutomatically = false
            userAgentString = userAgentString.replace("; wv", "").replace(" Version/4.0", "")
        }
        CookieManager.getInstance().setAcceptCookie(true)
        view.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(v: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                return !(url.startsWith("http://") || url.startsWith("https://") || url.startsWith("file:///android_asset/"))
            }

            override fun onPageFinished(v: WebView, url: String) {
                if (v === currentWeb()) {
                    address.setText(if (url.startsWith("file:///android_asset/orbit_home.html")) "" else url)
                    pageTitle.text = v.title ?: "Orbit"
                }
                if (!url.startsWith("file:///android_asset/")) saveHistoryItem(url, v.title ?: url)
            }

            override fun onReceivedError(v: WebView, request: WebResourceRequest, error: WebResourceError) {
                if (request.isForMainFrame && v === currentWeb()) {
                    showErrorPage(error.description?.toString() ?: "Не удалось загрузить страницу")
                }
            }
        }
        view.webChromeClient = object : WebChromeClient() {
            override fun onReceivedTitle(v: WebView, title: String) {
                if (v === currentWeb()) pageTitle.text = title
            }
        }
        view.setDownloadListener(DownloadListener { url, userAgent, contentDisposition, mimeType, _ ->
            runCatching {
                val fileName = android.webkit.URLUtil.guessFileName(url, contentDisposition, mimeType)
                val request = DownloadManager.Request(Uri.parse(url))
                    .setTitle(fileName)
                    .setDescription("Orbit Browser")
                    .setMimeType(mimeType)
                    .addRequestHeader("User-Agent", userAgent)
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                    .setDestinationInExternalPublicDir(android.os.Environment.DIRECTORY_DOWNLOADS, fileName)
                (getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager).enqueue(request)
                notifyUser("Загрузка началась", fileName)
            }.onFailure {
                notifyUser("Ошибка", "Не удалось начать загрузку")
            }
        })
    }

    private fun navigate() {
        val query = address.text.toString().trim()
        if (query.isBlank()) return
        val target = when {
            query.startsWith("http://") || query.startsWith("https://") -> query
            query.startsWith("file:///android_asset/") -> query
            query.contains(".") && !query.contains(" ") -> "https://$query"
            else -> searchUrl(query)
        }
        currentWeb()?.loadUrl(target) ?: addTab(target)
    }

    private fun showHome() {
        showBrowser()
        currentWeb()?.loadUrl("file:///android_asset/orbit_home.html")
    }

    private fun searchUrl(query: String): String {
        val encoded = URLEncoder.encode(query, "UTF-8")
        return "https://www.google.com/search?q=$encoded"
    }

    private fun showSimple(kind: String) {
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(22, 24, 22, 24)
            setBackgroundColor(orbitBg)
        }
        panel.addView(TextView(this).apply {
            text = when (kind) { "bookmarks" -> "Закладки"; "history" -> "История"; else -> "Загрузки" }
            textSize = 26f
            setTextColor(orbitTextColor)
            typeface = Typeface.DEFAULT_BOLD
        })
        val bodyText = TextView(this).apply {
            setPadding(0, 16, 0, 16)
            setTextColor(orbitMuted)
            this.text = when (kind) {
                "bookmarks" -> "Закладки синхронизируются с Orbit Account.\n\nДобавляйте страницы из браузера, чтобы видеть их здесь."
                "history" -> "История хранится локально и синхронизируется после входа в Orbit Account."
                else -> "Загрузки используют системный Download Manager Android."
            }
        }
        panel.addView(bodyText)
        val backButton = Button(this).apply { text = "← Orbit"; setOnClickListener { showHome() } }
        panel.addView(backButton)
        content.removeAllViews()
        content.addView(panel, FrameLayout.LayoutParams(-1, -1))
    }

    private fun showGames() {
        showBrowser()
        currentWeb()?.loadUrl("file:///android_asset/offline.html")
    }

    private fun showErrorPage(message: String) {
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(28, 28, 28, 28)
            setBackgroundColor(orbitBg)
        }
        panel.addView(TextView(this).apply {
            text = "Не удалось открыть страницу"
            textSize = 24f
            gravity = Gravity.CENTER
            setTextColor(orbitTextColor)
            typeface = Typeface.DEFAULT_BOLD
        })
        panel.addView(TextView(this).apply {
            text = message
            textSize = 14f
            gravity = Gravity.CENTER
            setTextColor(orbitMuted)
            setPadding(0, 12, 0, 20)
        })
        panel.addView(Button(this).apply {
            text = "Повторить"
            setOnClickListener { currentWeb()?.reload() ?: showHome() }
        })
        panel.addView(Button(this).apply {
            text = "На главную"
            setOnClickListener { showHome() }
        })
        content.removeAllViews()
        content.addView(panel, FrameLayout.LayoutParams(-1, -1))
    }

    private fun notifyUser(title: String, message: String, duration: Long = 2800L) {
        val card = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(18, 12, 18, 12)
            setBackgroundColor(orbitSurface2)
            elevation = 18f
        }
        card.addView(TextView(this).apply {
            text = title
            textSize = 13f
            setTextColor(orbitAccent2)
            typeface = Typeface.DEFAULT_BOLD
        })
        card.addView(TextView(this).apply {
            text = message
            textSize = 12f
            setTextColor(orbitTextColor)
            setPadding(0, 4, 0, 0)
        })
        val width = (resources.displayMetrics.widthPixels * 0.78f).toInt().coerceAtMost(360)
        val popup = PopupWindow(card, width, ViewGroup.LayoutParams.WRAP_CONTENT, false).apply {
            isOutsideTouchable = false
            isFocusable = false
            elevation = 18f
        }
        card.alpha = 0f
        popup.showAtLocation(root, Gravity.BOTTOM or Gravity.END, 14, 78)
        card.animate().alpha(1f).setDuration(180).start()
        handler.postDelayed({
            card.animate().alpha(0f).setDuration(220).withEndAction { popup.dismiss() }.start()
        }, duration)
    }

    private fun addTab(url: String) {
        val view = WebView(this)
        configure(view)
        tabs.add(view)
        current = tabs.lastIndex
        showBrowser()
        view.loadUrl(url)
    }

    private fun currentWeb(): WebView? = tabs.getOrNull(current)

    private fun showBrowser() {
        val view = currentWeb() ?: return
        content.removeAllViews()
        content.addView(view, FrameLayout.LayoutParams(-1, -1))
        address.setText(view.url ?: "")
        pageTitle.text = view.title ?: "Orbit"
    }

    private fun showProfile() {
        val scroll = ScrollView(this)
        val panel = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(24, 28, 24, 24); setBackgroundColor(orbitBg) }
        val displayName = user?.optString("display_name").orEmpty().ifBlank { user?.optString("username").orEmpty() }
        panel.addView(TextView(this).apply {
            text = if (displayName.isBlank()) "Orbit Account" else displayName
            textSize = 28f
            setTextColor(orbitTextColor)
            typeface = Typeface.DEFAULT_BOLD
        })
        if (user == null) {
            panel.addView(TextView(this).apply { text = "Профиль не создаётся автоматически. Войдите или зарегистрируйтесь."; setTextColor(orbitMuted); setPadding(0, 10, 0, 18) })
            val email = field("Email")
            val pass = field("Пароль")
            val name = field("Имя пользователя для регистрации")
            pass.inputType = 0x81
            val row = LinearLayout(this)
            val login = Button(this).apply { text = "Войти" }
            val register = Button(this).apply { text = "Регистрация" }
            row.addView(login, LinearLayout.LayoutParams(0, 52, 1f))
            row.addView(register, LinearLayout.LayoutParams(0, 52, 1f))
            panel.addView(email); panel.addView(pass); panel.addView(name); panel.addView(row)
            login.setOnClickListener { auth(false, email.text.toString(), pass.text.toString(), name.text.toString()) }
            register.setOnClickListener { auth(true, email.text.toString(), pass.text.toString(), name.text.toString()) }
        } else {
            panel.addView(TextView(this).apply { text = "Роль: ${user!!.optString("role", "user")}"; setTextColor(orbitMuted); setPadding(0, 4, 0, 12) })
            panel.addView(TextView(this).apply { text = "Титулы"; textSize = 18f; setTextColor(orbitTextColor); typeface = Typeface.DEFAULT_BOLD; setPadding(0, 10, 0, 8) })
            val titles = TextView(this).apply { text = "Загрузка…"; setTextColor(orbitMuted); setPadding(0, 0, 0, 12) }
            panel.addView(titles)
            loadTitles(titles)
            val display = field("Имя", user!!.optString("display_name"))
            val bio = field("О себе", user!!.optString("bio"))
            bio.minLines = 3
            panel.addView(display); panel.addView(bio)

            panel.addView(TextView(this).apply {
                text = "Вариант интерфейса"
                textSize = 18f
                setTextColor(orbitTextColor)
                typeface = Typeface.DEFAULT_BOLD
                setPadding(0, 16, 0, 8)
            })
            val variants = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
            listOf(
                "BASE" to "Базовый",
                "GOOGLE" to "Как Google",
                "MINIMAL" to "Минимализм",
                "COMPACT" to "Компактный",
                "GLASS" to "Стекло"
            ).forEach { (key, label) ->
                variants.addView(Button(this).apply {
                    text = if (interfaceVariant == key) "✓ $label" else label
                    setOnClickListener { setInterfaceVariant(key) }
                })
            }
            panel.addView(variants)
            panel.addView(Button(this).apply { text = "Сохранить профиль"; setOnClickListener { saveProfile(display.text.toString(), bio.text.toString()) } })
            panel.addView(TextView(this).apply { text = "Синхронизация · в фоне"; setTextColor(orbitAccent2); setPadding(0, 16, 0, 10) })
            panel.addView(Button(this).apply { text = "Выйти"; setOnClickListener { prefs.edit().clear().apply(); token = null; user = null; showHome() } })
        }
        panel.addView(Button(this).apply { text = "← Orbit"; setOnClickListener { showHome() } })
        scroll.addView(panel)
        content.removeAllViews()
        content.addView(scroll, FrameLayout.LayoutParams(-1, -1))
    }

    private fun field(hint: String, value: String = "") = EditText(this).apply {
        this.hint = hint
        setText(value)
        setHintTextColor(orbitMuted)
        setTextColor(orbitTextColor)
        setSingleLine(false)
        setBackgroundColor(orbitSurface2)
        setPadding(16, 10, 16, 10)
    }

    private fun isOnline(): Boolean {
        val manager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = manager.activeNetwork ?: return false
        val caps = manager.getNetworkCapabilities(network) ?: return false
        return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    private fun auth(register: Boolean, email: String, password: String, username: String) {
        executor.execute {
            runCatching {
                val body = JSONObject().put("email", email).put("password", password)
                if (register) body.put("username", username)
                http(if (register) "/api/auth/register" else "/api/auth/login", "POST", body)
            }.onSuccess { result ->
                token = result.optString("token").takeIf { it.isNotBlank() }
                user = result.optJSONObject("user")
                prefs.edit().putString("token", token).putString("profile", user?.toString()).apply()
                runOnUiThread { showProfile(); sync(true) }
            }.onFailure { error ->
                runOnUiThread { notifyUser("Ошибка входа", error.message ?: "Неизвестная ошибка", 4200) }
            }
        }
    }

    private fun loadTitles(view: TextView) {
        val currentToken = token ?: run { view.text = "Войдите, чтобы получить титулы."; return }
        executor.execute {
            runCatching { http("/api/profile/titles", "GET", null, currentToken) }
                .onSuccess { out ->
                    val titles = out.optJSONArray("titles") ?: JSONArray()
                    val equipped = out.optString("equipped", "Explorer")
                    val lines = mutableListOf<String>()
                    for (i in 0 until titles.length()) {
                        val item = titles.optJSONObject(i) ?: continue
                        val name = item.optString("name_ru", "Без названия")
                        val unlocked = item.optBoolean("unlocked", false)
                        lines += (if (unlocked) "✓ " else "○ ") + name + if (unlocked && name == equipped) "  • Надет" else ""
                    }
                    runOnUiThread { view.text = if (lines.isEmpty()) "Титулы пока недоступны." else lines.joinToString("\n") }
                }
                .onFailure { runOnUiThread { view.text = "Не удалось загрузить титулы." } }
        }
    }

    private fun saveProfile(display: String, bio: String) {
        val currentToken = token ?: return
        executor.execute {
            runCatching {
                val body = JSONObject().put("display_name", display).put("bio", bio).put("profile_theme", user?.optString("profile_theme", "VOID"))
                http("/api/profile", "PATCH", body, currentToken)
            }.onSuccess { out ->
                user = out.optJSONObject("user")
                prefs.edit().putString("profile", user?.toString()).apply()
                runOnUiThread { notifyUser("Профиль сохранён", "Изменения синхронизированы"); showProfile() }
                sync(true)
            }.onFailure { runOnUiThread { notifyUser("Ошибка", "Не удалось сохранить профиль") } }
        }
    }

    private fun sync(force: Boolean) {
        val currentToken = token ?: return
        executor.execute {
            runCatching {
                val state = JSONObject().put("user", user ?: JSONObject()).put("history", loadHistory()).put("bookmarks", loadBookmarks())
                http("/api/sync/state", "POST", JSONObject().put("state", state), currentToken)
            }
        }
    }

    private fun http(path: String, method: String, body: JSONObject? = null, bearer: String? = token): JSONObject {
        val connection = URL(api + path).openConnection() as HttpURLConnection
        connection.requestMethod = method
        connection.connectTimeout = 2500
        connection.readTimeout = 3500
        connection.setRequestProperty("Content-Type", "application/json")
        if (bearer != null) connection.setRequestProperty("Authorization", "Bearer $bearer")
        if (body != null) {
            connection.doOutput = true
            connection.outputStream.use { it.write(body.toString().toByteArray()) }
        }
        val responseText = (if (connection.responseCode >= 400) connection.errorStream else connection.inputStream).bufferedReader().use { it.readText() }
        if (connection.responseCode >= 400) throw IllegalStateException(responseText)
        return JSONObject(responseText)
    }

    private fun saveHistoryItem(url: String, title: String) {
        if (url.startsWith("file:///android_asset/")) return
        val items = loadHistory()
        for (i in items.length() - 1 downTo 0) if (items.optJSONObject(i)?.optString("url") == url) items.remove(i)
        val updated = JSONArray().put(JSONObject().put("url", url).put("title", title).put("timestamp", System.currentTimeMillis()))
        for (i in 0 until minOf(items.length(), 199)) updated.put(items.opt(i))
        prefs.edit().putString("history", updated.toString()).apply()
    }

    private fun loadHistory(): JSONArray = runCatching { JSONArray(prefs.getString("history", "[]") ?: "[]") }.getOrElse { JSONArray() }
    private fun saveHistory(items: JSONArray?) { if (items != null) prefs.edit().putString("history", items.toString()).apply() }
    private fun loadBookmarks(): JSONArray = runCatching { JSONArray(prefs.getString("bookmarks", "[]") ?: "[]") }.getOrElse { JSONArray() }
    private fun saveBookmarks(items: JSONArray?) { if (items != null) prefs.edit().putString("bookmarks", items.toString()).apply() }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        tabs.forEach { it.stopLoading(); it.destroy() }
        executor.shutdownNow()
        super.onDestroy()
    }
}
