package com.orbit.browser

import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.graphics.Color
import android.graphics.Typeface
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
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.*
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URLEncoder
import java.net.URL
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    private val api = "https://orbit-api-9uqa.onrender.com"
    private val appVersion = "1.0.0"
    private lateinit var root: LinearLayout
    private lateinit var tabsRow: LinearLayout
    private lateinit var address: EditText
    private lateinit var title: TextView
    private lateinit var content: FrameLayout
    private val tabs = mutableListOf<WebView>()
    private var current = -1
    private val purple = Color.rgb(155, 124, 255)
    private val bg = Color.rgb(7, 8, 18)
    private val surface = Color.rgb(16, 18, 37)
    private val surface2 = Color.rgb(24, 26, 50)
    private val text = Color.rgb(245, 243, 255)
    private val muted = Color.rgb(157, 154, 180)
    private val prefs by lazy { getSharedPreferences("orbit", Context.MODE_PRIVATE) }
    private val executor = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())
    private var user: JSONObject? = null
    private var token: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        token = prefs.getString("token", null)
        buildUi()
        showWelcome()
        if (isOnline()) addTab("https://html.duckduckgo.com/html/") else showOffline()
        sync(true)
        handler.postDelayed(object : Runnable {
            override fun run() {
                sync(false)
                handler.postDelayed(this, 10000)
            }
        }, 10000)
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                val v = currentWeb()
                if (v != null && v.canGoBack()) v.goBack() else showBrowser()
            }
        })
    }

    private fun buildUi() {
        root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setBackgroundResource(com.orbit.browser.R.drawable.orbit_root_bg) }
        setContentView(root)
        val top = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(10, 8, 10, 6); setBackgroundColor(surface) }
        val brand = TextView(this).apply { text = "✦  ORBIT"; setTextColor(text); textSize = 18f; gravity = Gravity.CENTER_VERTICAL; setTextColor(Color.WHITE); setTypeface(typeface, Typeface.BOLD) }
        top.addView(brand, LinearLayout.LayoutParams(-1, 40))
        tabsRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        top.addView(tabsRow, LinearLayout.LayoutParams(-1, 42))
        val bar = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        fun button(s: String, action: () -> Unit) = TextView(this).apply { text = s; textSize = 20f; gravity = Gravity.CENTER; setTextColor(text); setPadding(10, 0, 10, 0); setOnClickListener { action() } }
        bar.addView(button("‹") { currentWeb()?.goBack() }, LinearLayout.LayoutParams(44, 50))
        bar.addView(button("›") { currentWeb()?.goForward() }, LinearLayout.LayoutParams(44, 50))
        bar.addView(button("↻") { currentWeb()?.reload() }, LinearLayout.LayoutParams(44, 50))
        address = EditText(this).apply {
            hint = "Поиск или адрес"; hintTextColor = muted; setTextColor(text); textSize = 15f; setSingleLine(true); setPadding(18, 0, 18, 0); setBackgroundColor(surface2)
            setOnEditorActionListener { _, _, _ -> navigate(); true }
        }
        bar.addView(address, LinearLayout.LayoutParams(0, 50, 1f))
        bar.addView(button("＋") { addTab("https://html.duckduckgo.com/html/") }, LinearLayout.LayoutParams(44, 50))
        bar.addView(button("●") { showProfile() }, LinearLayout.LayoutParams(44, 50))
        top.addView(bar)
        title = TextView(this).apply { textSize = 11f; setTextColor(muted); setPadding(12, 0, 12, 4) }
        top.addView(title, LinearLayout.LayoutParams(-1, 28))
        root.addView(top)
        content = FrameLayout(this)
        root.addView(content, LinearLayout.LayoutParams(-1, 0, 1f))
    }

    private fun showWelcome() {
        val overlay = FrameLayout(this).apply { setBackgroundColor(bg); elevation = 100f }
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; gravity = Gravity.CENTER }
        val w = TextView(this).apply { text = "WELCOM"; textSize = 46f; setTextColor(text); gravity = Gravity.CENTER; typeface = Typeface.create("sans-serif", Typeface.BOLD) }
        val sub = TextView(this).apply { text = "ORBIT BROWSER"; textSize = 11f; setTextColor(purple); gravity = Gravity.CENTER; letterSpacing = .25f }
        box.addView(w); box.addView(sub)
        overlay.addView(box, FrameLayout.LayoutParams(-1, -1))
        content.addView(overlay, FrameLayout.LayoutParams(-1, -1))
        w.alpha = 0f; sub.alpha = 0f
        w.animate().alpha(1f).setDuration(420).withEndAction { sub.animate().alpha(1f).setDuration(350).withEndAction { overlay.animate().alpha(0f).setDuration(450).withEndAction { content.removeView(overlay) } } }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configure(v: WebView) {
        v.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            cacheMode = WebSettings.LOAD_DEFAULT
            builtInZoomControls = false
            displayZoomControls = false
            setSupportZoom(true)
            setSupportMultipleWindows(false)
            javaScriptCanOpenWindowsAutomatically = false
            userAgentString = userAgentString + " OrbitBrowser/1.0.0"
        }
        CookieManager.getInstance().setAcceptCookie(true)
        v.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val u = request.url.toString()
                if (u.startsWith("http://") || u.startsWith("https://")) return false
                return true
            }
            override fun onPageFinished(view: WebView, url: String) {
                if (view === currentWeb()) { address.setText(url); title.text = view.title ?: "Orbit" }
                if (!url.startsWith("file:///android_asset/offline.html")) saveHistory(url, view.title ?: url)
            }
            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: android.webkit.WebResourceError) {
                if (request.isForMainFrame) showOffline()
            }
        }
        v.webChromeClient = object : WebChromeClient() {
            override fun onReceivedTitle(view: WebView, pageTitle: String) { if (view === currentWeb()) title.text = pageTitle }
        }
        v.setDownloadListener(DownloadListener { _, url, userAgent, contentDisposition, mimeType ->
            try {
                val fileName = android.webkit.URLUtil.guessFileName(url, contentDisposition, mimeType)
                val request = DownloadManager.Request(Uri.parse(url))
                    .setTitle(fileName)
                    .setDescription("Orbit Browser")
                    .setMimeType(mimeType)
                    .addRequestHeader("User-Agent", userAgent)
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                    .setDestinationInExternalPublicDir(android.os.Environment.DIRECTORY_DOWNLOADS, fileName)
                val manager = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                manager.enqueue(request)
                Toast.makeText(this, "Загрузка началась: $fileName", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Toast.makeText(this, "Не удалось начать загрузку", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun isOnline(): Boolean {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
        val network = cm.activeNetwork ?: return false
        val caps = cm.getNetworkCapabilities(network) ?: return false
        return caps.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    private fun showOffline() {
        currentWeb()?.stopLoading()
        content.removeAllViews()
        val offline = WebView(this)
        configure(offline)
        content.addView(offline, FrameLayout.LayoutParams(-1, -1))
        offline.loadUrl("file:///android_asset/offline.html")
    }

    private fun addTab(url: String) {
        val v = WebView(this); configure(v); tabs.add(v); current = tabs.lastIndex; showBrowser(); v.loadUrl(url); refreshTabs()
    }
    private fun currentWeb(): WebView? = if (current in tabs.indices) tabs[current] else null
    private fun showBrowser() {
        content.removeAllViews(); val v=currentWeb() ?: return; content.addView(v, FrameLayout.LayoutParams(-1,-1)); address.setText(v.url ?: ""); title.text=v.title ?: "Orbit"; refreshTabs()
    }
    private fun refreshTabs() {
        tabsRow.removeAllViews()
        tabs.forEachIndexed { i, v ->
            val t=TextView(this).apply { text=(v.title?.takeIf{it.isNotBlank()} ?: "Новая вкладка").take(16)+"  ×"; textSize=12f; gravity=Gravity.CENTER; setTextColor(if(i==current) text else muted); setPadding(12,0,12,0); setOnClickListener{current=i;showBrowser()}; setOnLongClickListener{closeTab(i);true} }
            tabsRow.addView(t,LinearLayout.LayoutParams(0,42,1f))
        }
    }
    private fun closeTab(i:Int){ if(tabs.size<=1)return; tabs[i].stopLoading(); tabs[i].destroy(); tabs.removeAt(i); current=(current.coerceAtMost(tabs.lastIndex)); showBrowser() }

    private fun navigate() {
        var q=address.text.toString().trim(); if(q.isEmpty()) return
        val u=when { q.startsWith("http://")||q.startsWith("https://")->q; q.contains(".")&&!q.contains(" ")->"https://$q"; else->"https://html.duckduckgo.com/html/?q="+URLEncoder.encode(q,"UTF-8") }
        currentWeb()?.loadUrl(u) ?: addTab(u)
    }

    private fun showProfile() {
        val panel=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(24,28,24,24); setBackgroundColor(bg) }
        val head=TextView(this).apply{ text=if(user==null) "Orbit Account" else (user?.optString("display_name",user?.optString("username","Orbit"))); textSize=28f; setTextColor(text); typeface=Typeface.DEFAULT_BOLD }
        panel.addView(head)
        if(user==null){
            val info=TextView(this).apply{text="В аккаунт пока не входили. Профиль не создаётся автоматически."; setTextColor(muted); setPadding(0,10,0,18)}; panel.addView(info)
            val email=EditText(this).apply{hint="Email";setTextColor(text);hintTextColor=muted}; panel.addView(email)
            val pass=EditText(this).apply{hint="Пароль";setTextColor(text);hintTextColor=muted}; panel.addView(pass)
            val name=EditText(this).apply{hint="Имя пользователя для регистрации";setTextColor(text);hintTextColor=muted}; panel.addView(name)
            val row=LinearLayout(this); val login=Button(this).apply{text="Войти"}; val reg=Button(this).apply{text="Регистрация"}; row.addView(login,LinearLayout.LayoutParams(0,52,1f));row.addView(reg,LinearLayout.LayoutParams(0,52,1f));panel.addView(row)
            login.setOnClickListener{auth(false,email.text.toString(),pass.text.toString(),name.text.toString())}; reg.setOnClickListener{auth(true,email.text.toString(),pass.text.toString(),name.text.toString())}
        } else {
            val role=TextView(this).apply{text="Роль: "+user!!.optString("role","user");setTextColor(muted);setPadding(0,4,0,12)};panel.addView(role)
            val display=EditText(this).apply{setText(user!!.optString("display_name"));setTextColor(text);hintTextColor=muted;hint="Имя"};panel.addView(display)
            val bio=EditText(this).apply{setText(user!!.optString("bio"));setTextColor(text);hintTextColor=muted;hint="О себе";minLines=3};panel.addView(bio)
            val save=Button(this).apply{text="Сохранить"}; panel.addView(save); save.setOnClickListener{saveProfile(display.text.toString(),bio.text.toString())}
            val sync=TextView(this).apply{text="Синхронизация активна";setTextColor(purple);setPadding(0,16,0,10)};panel.addView(sync)
            val logout=Button(this).apply{text="Выйти"};panel.addView(logout);logout.setOnClickListener{prefs.edit().clear().apply();token=null;user=null;showBrowser()}
        }
        val back=Button(this).apply{text="← Назад"};panel.addView(back);back.setOnClickListener{showBrowser()}
        content.removeAllViews();content.addView(panel,FrameLayout.LayoutParams(-1,-1))
    }

    private fun auth(register:Boolean,email:String,password:String,username:String){
        executor.execute{
            try{
                val body=JSONObject().put("email",email).put("password",password); if(register) body.put("username",username)
                val result=http(if(register) "/api/auth/register" else "/api/auth/login","POST",body)
                runOnUiThread{ token=result.optString("token").takeIf{it.isNotBlank()}; user=result.optJSONObject("user"); if(token!=null){prefs.edit().putString("token",token).apply();showProfile();sync(true)} }
            }catch(e:Exception){runOnUiThread{Toast.makeText(this,"Ошибка входа: ${e.message}",Toast.LENGTH_LONG).show()}}
        }
    }

    private fun saveProfile(display:String,bio:String){
        val t=token?:return
        executor.execute{
            try{val body=JSONObject().put("display_name",display).put("bio",bio).put("profile_theme",user?.optString("profile_theme","VOID")); val out=http("/api/profile","PATCH",body,t);user=out.optJSONObject("user");runOnUiThread{prefs.edit().putString("profile",user?.toString()).apply();Toast.makeText(this,"Профиль сохранён и синхронизирован",Toast.LENGTH_SHORT).show();showProfile()};sync(true)}catch(e:Exception){runOnUiThread{Toast.makeText(this,"Не удалось сохранить профиль",Toast.LENGTH_SHORT).show()}}
        }
    }

    private fun sync(force:Boolean){
        val t=token?:return
        executor.execute{
            try{
                val state=JSONObject().put("user",user?:JSONObject()).put("history",loadHistory()).put("bookmarks",loadBookmarks())
                val out=http("/api/sync/state","POST",JSONObject().put("state",state),t)
                val remote=out.optJSONObject("state"); if(remote!=null){user=remote.optJSONObject("user")?:user; saveHistory(remote.optJSONArray("history"));saveBookmarks(remote.optJSONArray("bookmarks"));runOnUiThread{}}
            }catch(_:Exception){}
        }
    }

    private fun http(path:String,method:String,body:JSONObject?=null,bearer:String?=token):JSONObject{
        val c=(URL(api+path).openConnection() as HttpURLConnection);c.requestMethod=method;c.connectTimeout=8000;c.readTimeout=8000;c.setRequestProperty("Content-Type","application/json");if(bearer!=null)c.setRequestProperty("Authorization","Bearer $bearer");if(body!=null){c.doOutput=true;c.outputStream.use{it.write(body.toString().toByteArray())}};val text=(if(c.responseCode>=400)c.errorStream else c.inputStream).bufferedReader().use{it.readText()};if(c.responseCode>=400)throw IllegalStateException(text);return JSONObject(text)
    }

    private fun saveHistory(items:JSONArray?){ if(items==null)return; prefs.edit().putString("history",items.toString()).apply() }
    private fun loadHistory():JSONArray{ return try{JSONArray(prefs.getString("history","[]")?:"[]")}catch(_:Exception){JSONArray()} }
    private fun saveBookmarks(items:JSONArray?){ if(items==null)return; prefs.edit().putString("bookmarks",items.toString()).apply() }
    private fun loadBookmarks():JSONArray{ return try{JSONArray(prefs.getString("bookmarks","[]")?:"[]")}catch(_:Exception){JSONArray()} }

    override fun onDestroy(){ handler.removeCallbacksAndMessages(null); tabs.forEach{it.stopLoading();it.destroy()}; executor.shutdownNow(); super.onDestroy() }
}
