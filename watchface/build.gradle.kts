plugins {
    id("com.android.application")
}

android {
    namespace = "com.kaio.relogio.trico"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.kaio.relogio.trico"
        minSdk = 34
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
