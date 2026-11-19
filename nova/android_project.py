"""ساخت یک پروژهٔ کامل Android Studio (Gradle) از برنامهٔ Nova."""

import os
import re
from xml.sax.saxutils import escape

from .codegen_kotlin import activity_file, program_file, runtime_file

AGP_VERSION = "8.5.2"
KOTLIN_VERSION = "2.0.21"
GRADLE_VERSION = "8.7"
COMPOSE_BOM = "2024.09.03"

SETTINGS = """\
pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}
rootProject.name = "{name}"
include(":app")
"""

ROOT_BUILD = f"""\
plugins {{
    id("com.android.application") version "{AGP_VERSION}" apply false
    id("org.jetbrains.kotlin.android") version "{KOTLIN_VERSION}" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "{KOTLIN_VERSION}" apply false
}}
"""

APP_BUILD = """\
plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}}

android {{
    namespace = "{package}"
    compileSdk = 34

    defaultConfig {{
        applicationId = "{package}"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
        }}
    }}
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
    kotlinOptions {{
        jvmTarget = "17"
    }}
    buildFeatures {{
        compose = true
    }}
}}

dependencies {{
    implementation(platform("androidx.compose:compose-bom:{bom}"))
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
}}
"""

MANIFEST = """\
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.Material.Light.NoActionBar">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

STRINGS = """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{title}</string>
</resources>
"""

GRADLE_PROPERTIES = """\
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
"""

WRAPPER_PROPERTIES = f"""\
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-{GRADLE_VERSION}-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""

README = """\
# {title}

این پروژه به‌صورت خودکار توسط کامپایلر **Nova** از فایل `{source}` ساخته شده است.

## اجرا
1. پوشه را در Android Studio باز کنید (File > Open).
2. صبر کنید تا Gradle Sync تمام شود.
3. یک شبیه‌ساز یا گوشی وصل کنید و دکمهٔ Run را بزنید.

یا از خط فرمان (اگر Gradle نصب است):  `gradle :app:assembleDebug`

فایل‌های تولیدشده:
- `app/src/main/java/{path}/MainActivity.kt`: صفحه‌ها (Jetpack Compose) و ناوبری
- `app/src/main/java/{path}/Program.kt`: توابع و متغیرهای سراسری
- `app/src/main/java/{path}/NovaRuntime.kt`: کتابخانهٔ زمان اجرا
"""

GITIGNORE = """\
.gradle/
build/
local.properties
.idea/
*.iml
"""


def android_string(s):
    s = escape(s).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
    if s[:1] in ("@", "?"):
        s = "\\" + s
    return s


def valid_package(p):
    return re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", p) is not None


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def generate(prog, out_dir, package, source_name="app.nova"):
    if not valid_package(package):
        raise ValueError(f"invalid package name '{package}' (example: com.example.myapp)")
    title = prog.app.title
    pkg_path = package.replace(".", "/")
    src = os.path.join(out_dir, "app", "src", "main")
    java = os.path.join(src, "java", pkg_path)
    project_name = re.sub(r"[^A-Za-z0-9_-]", "", package.split(".")[-1]) or "NovaApp"

    files = {
        "settings.gradle.kts": SETTINGS.format(name=project_name),
        "build.gradle.kts": ROOT_BUILD,
        "gradle.properties": GRADLE_PROPERTIES,
        "gradle/wrapper/gradle-wrapper.properties": WRAPPER_PROPERTIES,
        ".gitignore": GITIGNORE,
        "README.md": README.format(title=title, source=source_name, path=pkg_path),
        "app/build.gradle.kts": APP_BUILD.format(package=package, bom=COMPOSE_BOM),
        "app/src/main/AndroidManifest.xml": MANIFEST,
        "app/src/main/res/values/strings.xml": STRINGS.format(title=android_string(title)),
    }
    for rel, content in files.items():
        write(os.path.join(out_dir, rel), content)
    write(os.path.join(java, "MainActivity.kt"), activity_file(prog, package))
    write(os.path.join(java, "Program.kt"), program_file(prog, package))
    write(os.path.join(java, "NovaRuntime.kt"), runtime_file(package))
    return out_dir
