plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "com.orbit.browser"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.orbit.browser"
        minSdk = 26
        targetSdk = 35
        versionCode = 169
        versionName = "1.16.17"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
}
dependencies { implementation("androidx.core:core-ktx:1.15.0"); implementation("androidx.appcompat:appcompat:1.7.0"); implementation("androidx.activity:activity-ktx:1.10.1") }
