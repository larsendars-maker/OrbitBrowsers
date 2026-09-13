package com.orbit.browser

import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var web: WebView
    private lateinit var topBar: LinearLayout
    private var panelHidden = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = FrameLayout(this)
        root.setBackgroundColor(Color.rgb(7, 5, 17))

        web = WebView(this)
        web.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                injectPanelToggle()
            }
        }
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.cacheMode = WebSettings.LOAD_DEFAULT
        web.settings.loadsImagesAutomatically = true
        web.settings.databaseEnabled = true

        root.addView(web, FrameLayout.LayoutParams(-1, -1))

        topBar = LinearLayout(this)
        topBar.orientation = LinearLayout.HORIZONTAL
        topBar.gravity = Gravity.CENTER_VERTICAL
        topBar.setPadding(16, 8, 12, 8)
        topBar.setBackgroundColor(Color.rgb(12, 8, 22))

        val title = Button(this)
        title.text = "ORBIT"
        title.setTextColor(Color.WHITE)
        title.setBackgroundColor(Color.TRANSPARENT)
        title.isAllCaps = false
        topBar.addView(title, LinearLayout.LayoutParams(0, 56, 1f))

        val toggle = Button(this)
        toggle.text = "☰"
        toggle.setTextColor(Color.WHITE)
        toggle.setOnClickListener {
            panelHidden = !panelHidden
            web.evaluateJavascript(
                "window.orbitTogglePanel && window.orbitTogglePanel(${if (panelHidden) "true" else "false"})",
                null
            )
            toggle.text = if (panelHidden) "☰" else "×"
        }
        topBar.addView(toggle, LinearLayout.LayoutParams(64, 56))

        val lp = FrameLayout.LayoutParams(-1, 72)
        lp.gravity = Gravity.TOP
        root.addView(topBar, lp)

        val webLp = web.layoutParams as FrameLayout.LayoutParams
        webLp.topMargin = 72
        web.layoutParams = webLp

        setContentView(root)
        web.loadUrl("https://orbit-api-9uqa.onrender.com/")
    }

    private fun injectPanelToggle() {
        web.evaluateJavascript(
            """
            (function(){
              if(window.orbitTogglePanel) return;
              window.orbitTogglePanel=function(hide){
                document.documentElement.classList.toggle('orbit-panel-hidden', !!hide);
                var nav=document.querySelector('.nav');
                if(nav) nav.style.display = hide ? 'none' : '';
                var side=document.querySelector('#sidebar,.sidebar,.orbit-sidebar');
                if(side) side.style.display = hide ? 'none' : '';
              };
            })();
            """.trimIndent(), null
        )
    }

    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }
}
