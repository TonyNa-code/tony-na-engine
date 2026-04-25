from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path


ASSET_TYPE_IMAGE = {"background", "sprite", "cg", "ui"}
DEFAULT_GAME_DATA_NAME = "game_data.json"
ENGINE_BRAND_LOGO_RELATIVE_PATH = "assets/brand-logo.png"
NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME = "requirements-native-runtime-video.txt"
NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_CANDIDATES = (NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME, "requirements-video.txt")
GAME_UI_ASSET_REFERENCE_LABELS = {
    "titleBackgroundAssetId": "标题背景",
    "titleLogoAssetId": "标题 Logo",
    "panelFrameAssetId": "通用面板九宫格",
    "buttonFrameAssetId": "按钮默认九宫格",
    "buttonHoverFrameAssetId": "按钮悬停九宫格",
    "buttonPressedFrameAssetId": "按钮按下九宫格",
    "buttonDisabledFrameAssetId": "按钮禁用九宫格",
    "saveSlotFrameAssetId": "存档卡片九宫格",
    "systemPanelFrameAssetId": "系统面板九宫格",
    "uiOverlayAssetId": "UI 氛围叠层",
}
NATIVE_VIDEO_BACKEND_OPTIONS = [
    {
        "id": "system_player_bridge",
        "label": "系统播放器桥接",
        "kind": "external",
        "pythonPackage": "",
        "moduleName": "",
        "embeddedVideo": False,
        "audio": True,
        "productionReady": True,
        "notes": "默认方案。包体轻、三平台风险低，但无法在 Pygame 窗口内检测真实播放进度。",
    },
    {
        "id": "opencv_frame_preview",
        "label": "OpenCV 内嵌画面帧预览",
        "kind": "embedded_visual_preview",
        "pythonPackage": "opencv-python>=4.9,<5",
        "moduleName": "cv2",
        "embeddedVideo": True,
        "audio": False,
        "productionReady": False,
        "notes": "可作为后续窗口内嵌画面解码候选；OpenCV 不负责音频，正式 OP/ED 仍需额外音频/同步方案。",
    },
]
COLOR_BG = (12, 15, 28)
COLOR_PANEL = (18, 24, 40)
COLOR_PANEL_BORDER = (78, 106, 168)
COLOR_TEXT = (243, 246, 255)
COLOR_TEXT_MUTED = (160, 176, 204)
COLOR_ACCENT = (106, 154, 255)
COLOR_ACCENT_ALT = (173, 115, 255)
COLOR_WARNING = (255, 161, 110)
FPS = 60
SAVE_SHORTCUT_COUNT = 3
SAVE_DIALOG_PAGE_SIZE = 6
DEFAULT_FORMAL_SAVE_SLOT_COUNT = 24
MIN_FORMAL_SAVE_SLOT_COUNT = 3
MAX_FORMAL_SAVE_SLOT_COUNT = 120
DEFAULT_DIALOG_BOX_CONFIG = {
    "preset": "moonlight",
    "shape": "rounded",
    "widthPercent": 76,
    "minHeight": 148,
    "paddingX": 18,
    "paddingY": 14,
    "backgroundColor": "#0c1422",
    "backgroundOpacity": 92,
    "borderColor": "#79dcff",
    "borderOpacity": 18,
    "textColor": "#f3f6ff",
    "speakerColor": "#ffffff",
    "hintColor": "#c8d6ea",
    "blurStrength": 10,
    "borderWidth": 1,
    "shadowStrength": 30,
    "panelAssetId": "",
    "panelAssetOpacity": 0,
    "panelAssetFit": "cover",
    "anchor": "bottom",
    "offsetXPercent": 0,
    "offsetYPercent": 0,
}
DEFAULT_GAME_UI_CONFIG = {
    "preset": "stellar",
    "layoutPreset": "balanced",
    "titleLayout": "center",
    "fontStyle": "modern",
    "surfaceStyle": "glass",
    "brandMode": "project",
    "sidePanelMode": "full",
    "sidePanelPosition": "right",
    "topbarPosition": "top",
    "hudPosition": "top",
    "titleCardAnchor": "center",
    "titleCardOffsetXPercent": 0,
    "titleCardOffsetYPercent": 0,
    "layoutGap": 20,
    "sidePanelWidth": 320,
    "backgroundColor": "#071120",
    "backgroundAccentColor": "#6bd5ff",
    "panelColor": "#0c1422",
    "panelOpacity": 88,
    "textColor": "#f3f7ff",
    "mutedTextColor": "#bacce4",
    "accentColor": "#79dcff",
    "accentAltColor": "#7b7cff",
    "buttonTextColor": "#f8fcff",
    "borderColor": "#79dcff",
    "borderOpacity": 18,
    "cornerRadius": 22,
    "backdropBlur": 14,
    "stageVignette": 42,
    "motionIntensity": 70,
    "titleBackgroundAssetId": "",
    "titleBackgroundFit": "cover",
    "titleBackgroundOpacity": 42,
    "titleLogoAssetId": "",
    "panelFrameAssetId": "",
    "panelFrameOpacity": 18,
    "panelFrameSlice": {"top": 24, "right": 24, "bottom": 24, "left": 24},
    "buttonFrameAssetId": "",
    "buttonHoverFrameAssetId": "",
    "buttonPressedFrameAssetId": "",
    "buttonDisabledFrameAssetId": "",
    "buttonFrameOpacity": 24,
    "buttonFrameSlice": {"top": 18, "right": 18, "bottom": 18, "left": 18},
    "saveSlotFrameAssetId": "",
    "systemPanelFrameAssetId": "",
    "uiOverlayAssetId": "",
    "uiOverlayOpacity": 8,
}
DIALOG_BOX_PRESETS = {
    "moonlight": {
        "preset": "moonlight",
        "shape": "rounded",
        "widthPercent": 76,
        "minHeight": 148,
        "paddingX": 18,
        "paddingY": 14,
        "backgroundColor": "#0c1422",
        "backgroundOpacity": 92,
        "borderColor": "#79dcff",
        "borderOpacity": 18,
        "textColor": "#f3f6ff",
        "speakerColor": "#ffffff",
        "hintColor": "#c8d6ea",
        "blurStrength": 10,
        "borderWidth": 1,
        "shadowStrength": 30,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "warm": {
        "preset": "warm",
        "shape": "rounded",
        "widthPercent": 76,
        "minHeight": 148,
        "paddingX": 16,
        "paddingY": 14,
        "backgroundColor": "#fffaf5",
        "backgroundOpacity": 92,
        "borderColor": "#8f6548",
        "borderOpacity": 18,
        "textColor": "#332117",
        "speakerColor": "#7f5438",
        "hintColor": "#6d5b4f",
        "blurStrength": 8,
        "borderWidth": 1,
        "shadowStrength": 18,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "paper": {
        "preset": "paper",
        "shape": "square",
        "widthPercent": 76,
        "minHeight": 156,
        "paddingX": 18,
        "paddingY": 16,
        "backgroundColor": "#fff7e8",
        "backgroundOpacity": 95,
        "borderColor": "#b08659",
        "borderOpacity": 28,
        "textColor": "#4a2f1d",
        "speakerColor": "#7f5438",
        "hintColor": "#7f6a54",
        "blurStrength": 4,
        "borderWidth": 1,
        "shadowStrength": 16,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "transparent": {
        "preset": "transparent",
        "shape": "capsule",
        "widthPercent": 88,
        "minHeight": 132,
        "paddingX": 14,
        "paddingY": 10,
        "backgroundColor": "#08111b",
        "backgroundOpacity": 0,
        "borderColor": "#7fe6ff",
        "borderOpacity": 0,
        "textColor": "#f4f8ff",
        "speakerColor": "#ffffff",
        "hintColor": "#d0daf0",
        "blurStrength": 0,
        "borderWidth": 0,
        "shadowStrength": 0,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
}
SAVE_ROOT_DIR_NAME = ".tony-na-engine"
SAVE_SUBDIR_NAME = "native-runtime-saves"
SETTINGS_SUBDIR_NAME = "native-runtime-settings"
PROGRESS_SUBDIR_NAME = "native-runtime-progress"
PROFILE_SUBDIR_NAME = "native-runtime-profiles"
AUTO_RESUME_SUBDIR_NAME = "native-runtime-autoresume"
LOG_SUBDIR_NAME = "native-runtime-logs"
DEFAULT_RUNTIME_PLAYER_SETTINGS = {
    "themeMode": "auto",
    "displayMode": "windowed",
    "textSpeed": "normal",
    "masterVolume": 100,
    "bgmVolume": 85,
    "sfxVolume": 90,
    "voiceVolume": 100,
}
DEFAULT_PLAYER_PROFILE = {
    "firstPlayedAt": None,
    "lastPlayedAt": None,
    "lastEndedAt": None,
    "totalPlayMs": 0,
    "sessionCount": 0,
    "resumedCount": 0,
    "returnToTitleCount": 0,
}
RUNTIME_THEME_MODES = ("auto", "light", "dark")
RUNTIME_DISPLAY_MODES = ("windowed", "fullscreen")
TEXT_SPEED_PRESETS = {
    "slow": 24,
    "normal": 42,
    "fast": 72,
    "instant": 10000,
}
TEXT_SPEED_LABELS = {
    "slow": "慢",
    "normal": "标准",
    "fast": "快",
    "instant": "瞬时",
}
SYSTEM_MENU_ITEMS = [
    ("continue", "继续"),
    ("archives", "资料馆"),
    ("profile", "玩家档案"),
    ("auto-resume", "续玩记录"),
    ("save", "正式存档"),
    ("load", "读取存档"),
    ("settings", "体验设置"),
    ("quick-save", "快速存档"),
    ("quick-load", "快速读档"),
    ("restart", "回到开头"),
    ("exit", "退出预览"),
]
TITLE_MENU_ITEMS = [
    ("start", "开始游戏"),
    ("resume", "继续上次"),
    ("load", "读取存档"),
    ("settings", "体验设置"),
    ("archives", "资料馆"),
    ("exit", "退出"),
]
SETTINGS_MENU_ITEMS = [
    ("themeMode", "界面主题"),
    ("displayMode", "显示模式"),
    ("textSpeed", "文字速度"),
    ("masterVolume", "总音量"),
    ("bgmVolume", "BGM 音量"),
    ("sfxVolume", "音效音量"),
    ("voiceVolume", "语音音量"),
]
NATIVE_VIDEO_PREVIEW_MODE = "cinematic_bridge_card"
ARCHIVE_MENU_ITEMS = {
    "chapters": "章节回放",
    "music": "音乐鉴赏",
    "gallery": "CG 回想",
    "locations": "地点图鉴",
    "characters": "角色图鉴",
    "narrations": "旁白摘录",
    "relations": "关系图鉴",
    "voices": "语音回听",
    "endings": "结局回放",
    "achievements": "成就馆",
}
ARCHIVE_MENU_SEQUENCE = tuple(ARCHIVE_MENU_ITEMS.keys())
NATIVE_PARTICLE_PRESET_DEFAULTS = {
    "snow": {"density": 40, "sizeMin": 5, "sizeMax": 14, "speed": 90, "drift": 18, "color": (255, 255, 255), "accent": (214, 238, 255), "shape": "flake"},
    "rain": {"density": 54, "sizeMin": 2, "sizeMax": 4, "speed": 300, "drift": 32, "color": (164, 208, 255), "accent": (219, 239, 255), "shape": "rain"},
    "petals": {"density": 30, "sizeMin": 10, "sizeMax": 18, "speed": 84, "drift": 30, "color": (255, 191, 221), "accent": (255, 226, 238), "shape": "petal"},
    "dust": {"density": 24, "sizeMin": 3, "sizeMax": 8, "speed": 26, "drift": 10, "color": (244, 230, 191), "accent": (255, 245, 221), "shape": "glow"},
    "embers": {"density": 34, "sizeMin": 4, "sizeMax": 10, "speed": 72, "drift": 18, "color": (255, 142, 82), "accent": (255, 217, 148), "shape": "ember"},
    "sparkles": {"density": 22, "sizeMin": 6, "sizeMax": 12, "speed": 34, "drift": 12, "color": (175, 213, 255), "accent": (235, 243, 255), "shape": "spark"},
    "bubbles": {"density": 18, "sizeMin": 10, "sizeMax": 20, "speed": -42, "drift": 12, "color": (150, 220, 255), "accent": (239, 250, 255), "shape": "bubble"},
    "confetti": {"density": 28, "sizeMin": 6, "sizeMax": 12, "speed": 110, "drift": 42, "color": (118, 159, 255), "accent": (185, 115, 255), "shape": "confetti"},
    "smoke": {"density": 20, "sizeMin": 18, "sizeMax": 42, "speed": -24, "drift": 16, "color": (149, 164, 196), "accent": (214, 222, 242), "shape": "smoke"},
    "flame": {"density": 24, "sizeMin": 10, "sizeMax": 22, "speed": -110, "drift": 12, "color": (255, 132, 63), "accent": (255, 214, 104), "shape": "flame"},
    "stardust": {"density": 28, "sizeMin": 4, "sizeMax": 10, "speed": 20, "drift": 8, "color": (126, 173, 255), "accent": (201, 140, 255), "shape": "star"},
    "glyphs": {"density": 16, "sizeMin": 12, "sizeMax": 22, "speed": 12, "drift": 6, "color": (124, 167, 255), "accent": (196, 126, 255), "shape": "glyph"},
}
NATIVE_PARTICLE_INTENSITY_MULTIPLIER = {"light": 0.65, "medium": 1.0, "heavy": 1.45}
NATIVE_PARTICLE_SPEED_MULTIPLIER = {"slow": 0.72, "medium": 1.0, "fast": 1.35}
NATIVE_PARTICLE_WIND_VALUE = {"left": -26, "still": 0, "right": 26}
NATIVE_PARTICLE_AREA_RANGES = {
    "full": (0.04, 0.96),
    "left": (0.04, 0.46),
    "center": (0.28, 0.72),
    "right": (0.54, 0.96),
}
EFFECT_DURATION_SECONDS = {"short": 0.42, "medium": 0.72, "long": 1.2}
SHAKE_DISTANCE = {"light": 4, "medium": 9, "heavy": 16}
FLASH_COLORS = {"white": (255, 255, 255), "warm": (255, 206, 138), "red": (255, 94, 94), "black": (0, 0, 0)}
FLASH_ALPHA = {"soft": 86, "medium": 146, "strong": 210}
FADE_COLORS = {"black": (0, 0, 0), "white": (255, 255, 255)}
CAMERA_ZOOM_SCALE = {
    ("zoom_in", "light"): 1.045,
    ("zoom_in", "medium"): 1.085,
    ("zoom_in", "heavy"): 1.13,
    ("zoom_out", "light"): 0.985,
    ("zoom_out", "medium"): 0.96,
    ("zoom_out", "heavy"): 0.925,
}
CAMERA_PAN_OFFSET = {"left": 0.055, "right": -0.055}
CAMERA_PAN_STRENGTH_MULTIPLIER = {"light": 0.62, "medium": 1.0, "heavy": 1.44}
SCREEN_FILTER_WASH = {
    "memory": ((255, 207, 150), 38),
    "mono": ((180, 190, 205), 42),
    "dream": ((172, 145, 255), 44),
    "cold": ((122, 184, 255), 42),
}
SCREEN_FILTER_STRENGTH_MULTIPLIER = {"soft": 0.62, "medium": 1.0, "strong": 1.38}
DEPTH_BLUR_ALPHA = {"soft": 24, "medium": 42, "strong": 64}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
SUPPORTED_AUDIO_EXTENSIONS = {".ogg", ".wav", ".mp3"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}
LARGE_IMAGE_WARNING_BYTES = 18 * 1024 * 1024
LARGE_AUDIO_WARNING_BYTES = 30 * 1024 * 1024
LARGE_VIDEO_WARNING_BYTES = 300 * 1024 * 1024


class NativeRuntimeError(RuntimeError):
    pass


def load_game_data(game_data_path: Path) -> dict:
    if not game_data_path.is_file():
        raise NativeRuntimeError(f"没有找到游戏数据文件：{game_data_path}")
    return json.loads(game_data_path.read_text(encoding="utf-8"))


def resolve_default_game_data_path() -> Path:
    candidates: list[Path] = []
    packaged_base = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False):
        if packaged_base:
            candidates.append(Path(packaged_base) / DEFAULT_GAME_DATA_NAME)
        candidates.append(Path(sys.executable).resolve().parent / DEFAULT_GAME_DATA_NAME)
    candidates.append(Path.cwd() / DEFAULT_GAME_DATA_NAME)
    candidates.append(Path(__file__).resolve().parent / DEFAULT_GAME_DATA_NAME)
    if not getattr(sys, "frozen", False) and packaged_base:
        candidates.append(Path(packaged_base) / DEFAULT_GAME_DATA_NAME)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return candidates[0].resolve()


def resolve_game_data_argument(game_data_value: str) -> Path:
    candidate = Path(game_data_value)
    if game_data_value == DEFAULT_GAME_DATA_NAME and not candidate.is_file():
        return resolve_default_game_data_path()
    return candidate.resolve()


def get_external_video_opener_command(video_path: Path) -> list[str] | None:
    if sys.platform.startswith("win"):
        return None
    if sys.platform == "darwin":
        opener = shutil.which("open")
        return [opener or "open", str(video_path)]
    if sys.platform.startswith("linux"):
        opener = shutil.which("xdg-open")
        if opener:
            return [opener, str(video_path)]
        gio = shutil.which("gio")
        if gio:
            return [gio, "open", str(video_path)]
    return None


def get_external_video_opener_label() -> str:
    if sys.platform.startswith("win"):
        return "Windows 默认视频播放器"
    if sys.platform == "darwin":
        return "macOS 默认视频播放器"
    if sys.platform.startswith("linux"):
        if shutil.which("xdg-open"):
            return "Linux xdg-open 默认视频播放器"
        if shutil.which("gio"):
            return "Linux gio 默认视频播放器"
    return "系统默认视频播放器"


def can_open_external_video() -> bool:
    if sys.platform.startswith("win"):
        return hasattr(os, "startfile")
    return get_external_video_opener_command(Path("preview.mp4")) is not None


def is_optional_python_module_available(module_name: str) -> bool:
    if not module_name:
        return True
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def import_optional_python_module(module_name: str):
    if not module_name:
        return None
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


def get_native_video_backend_options(bundle_dir: Path | None = None) -> list[dict]:
    candidate_root = bundle_dir or Path(".")
    optional_requirements_name = next(
        (
            file_name
            for file_name in NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_CANDIDATES
            if (candidate_root / file_name).is_file()
        ),
        NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME,
    )
    options = []
    for option in NATIVE_VIDEO_BACKEND_OPTIONS:
        option_copy = dict(option)
        if option_copy["id"] == "system_player_bridge":
            available = can_open_external_video()
            option_copy.update(
                {
                    "available": available,
                    "status": "ready" if available else "needs_system_opener",
                    "openerLabel": get_external_video_opener_label() if available else "",
                    "installCommand": "",
                }
            )
        else:
            available = is_optional_python_module_available(str(option_copy.get("moduleName") or ""))
            option_copy.update(
                {
                    "available": available,
                    "status": "available" if available else "optional_dependency_missing",
                    "optionalRequirements": optional_requirements_name,
                    "installCommand": f"python -m pip install -r {optional_requirements_name}",
                }
            )
        options.append(option_copy)
    return options


def open_external_video(video_path: Path) -> tuple[bool, str]:
    if not video_path.is_file():
        return False, f"视频文件不存在：{video_path.name}"
    try:
        if sys.platform.startswith("win"):
            if not hasattr(os, "startfile"):
                return False, "当前 Windows Python 环境没有 os.startfile，无法唤起默认播放器。"
            os.startfile(str(video_path))  # type: ignore[attr-defined]
        else:
            command = get_external_video_opener_command(video_path)
            if not command:
                return False, "当前系统没有找到可用的默认视频打开器。"
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as error:
        return False, f"打开视频失败：{error}"
    return True, f"已交给{get_external_video_opener_label()}播放。"


def load_opencv_video_frame_surface(
    pygame,
    video_path: Path,
    start_time_seconds: float = 0.0,
    cv2_module=None,
) -> tuple[object | None, str]:
    cv2 = cv2_module if cv2_module is not None else import_optional_python_module("cv2")
    if cv2 is None:
        return None, "未安装 OpenCV：使用桥接卡"
    if not video_path.is_file():
        return None, "视频文件不存在"

    capture = None
    try:
        capture = cv2.VideoCapture(str(video_path))
        if hasattr(capture, "isOpened") and not capture.isOpened():
            return None, "OpenCV 无法打开视频"
        if start_time_seconds > 0 and hasattr(cv2, "CAP_PROP_POS_MSEC") and hasattr(capture, "set"):
            capture.set(cv2.CAP_PROP_POS_MSEC, float(start_time_seconds) * 1000.0)
        ok, frame = capture.read()
        if not ok or frame is None:
            return None, "OpenCV 未读取到画面帧"
        if hasattr(cv2, "cvtColor") and hasattr(cv2, "COLOR_BGR2RGB"):
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]
        if width <= 0 or height <= 0:
            return None, "视频帧尺寸无效"
        surface = pygame.image.frombuffer(frame.tobytes(), (int(width), int(height)), "RGB").copy()
        return surface, "OpenCV 帧预览"
    except Exception as error:
        return None, f"OpenCV 帧预览失败：{error}"
    finally:
        if capture is not None and hasattr(capture, "release"):
            try:
                capture.release()
            except Exception:
                pass


def validate_bundle(bundle_dir: Path) -> None:
    data_path = bundle_dir / DEFAULT_GAME_DATA_NAME
    payload = load_game_data(data_path)
    required_keys = {"project", "assets", "characters", "variables", "chapters"}
    missing_keys = sorted(required_keys - set(payload))
    if missing_keys:
        raise NativeRuntimeError(f"游戏数据缺少这些字段：{', '.join(missing_keys)}")

    chapters = payload.get("chapters") or []
    if not isinstance(chapters, list) or not chapters:
        raise NativeRuntimeError("游戏数据里没有任何章节。")

    assets = (payload.get("assets") or {}).get("assets") or []
    for asset in assets:
        export_url = str(asset.get("exportUrl") or "").strip()
        if not export_url or asset.get("isMissing"):
            continue
        if not (bundle_dir / export_url).is_file():
            raise NativeRuntimeError(f"导出资源不存在：{export_url}")


def add_release_check_issue(
    issues: list[dict],
    severity: str,
    code: str,
    message: str,
    suggestion: str = "",
    path: str = "",
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            "suggestion": suggestion,
            "path": path,
        }
    )


def get_release_check_status(issues: list[dict]) -> str:
    if any(issue.get("severity") == "error" for issue in issues):
        return "fail"
    if any(issue.get("severity") == "warning" for issue in issues):
        return "warn"
    return "pass"


def build_release_check_report(bundle_dir: Path) -> dict:
    issues: list[dict] = []
    data_path = bundle_dir / DEFAULT_GAME_DATA_NAME
    payload: dict | None = None
    try:
        payload = load_game_data(data_path)
    except Exception as error:
        add_release_check_issue(
            issues,
            "error",
            "game_data_missing_or_invalid",
            f"无法读取 {DEFAULT_GAME_DATA_NAME}：{error}",
            "重新导出原生 Runtime 包，确认 game_data.json 没有被移动或手动改坏。",
            DEFAULT_GAME_DATA_NAME,
        )
        return {
            "status": get_release_check_status(issues),
            "checkedAt": now_iso(),
            "bundleDir": str(bundle_dir),
            "projectTitle": "",
            "summary": {"errors": 1, "warnings": 0, "assetCount": 0, "sceneCount": 0},
            "issues": issues,
        }

    try:
        validate_bundle(bundle_dir)
    except NativeRuntimeError as error:
        add_release_check_issue(
            issues,
            "error",
            "bundle_validation_failed",
            str(error),
            "先修复导出包结构或缺失素材，再继续打包 App。",
            DEFAULT_GAME_DATA_NAME,
        )

    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    project_title = str(project.get("title") or project.get("name") or "未命名项目")
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    scenes = iter_export_scenes(chapters)
    scene_ids = {str(scene.get("id") or "") for scene in scenes if scene.get("id")}
    entry_scene_id = str(project.get("entrySceneId") or "").strip()
    if not scenes:
        add_release_check_issue(
            issues,
            "error",
            "no_scene",
            "项目里没有可播放场景。",
            "至少创建一个章节和一个场景，并设置入口场景。",
        )
    elif entry_scene_id and entry_scene_id not in scene_ids:
        add_release_check_issue(
            issues,
            "error",
            "entry_scene_missing",
            f"入口场景不存在：{entry_scene_id}",
            "在项目设置里重新选择一个仍然存在的入口场景。",
        )
    elif not entry_scene_id:
        add_release_check_issue(
            issues,
            "warning",
            "entry_scene_auto_fallback",
            "项目没有显式入口场景，Runtime 会自动使用第一个场景。",
            "正式发布前建议设置入口场景，避免章节排序变化后进入错误位置。",
        )

    dialogue_like_count = sum(
        1
        for scene in scenes
        for block in scene.get("blocks", []) or []
        if str(block.get("type") or "") in {"dialogue", "narration", "choice"}
    )
    if scenes and dialogue_like_count == 0:
        add_release_check_issue(
            issues,
            "warning",
            "no_dialogue_or_choice",
            "当前导出包没有检测到台词、旁白或选项块。",
            "如果这不是纯演出测试包，建议补一段可读剧情再发布。",
        )

    formal_slot_count = get_project_formal_save_slot_count(project)
    if formal_slot_count > 80:
        add_release_check_issue(
            issues,
            "warning",
            "many_save_slots",
            f"项目设置了 {formal_slot_count} 个正式存档位。",
            "大体量游戏可以保留；短篇游戏建议减少存档位，让读档界面更清爽。",
        )

    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    assets_by_id = {str(asset.get("id")): asset for asset in assets if isinstance(asset, dict) and asset.get("id")}
    game_ui_config = project.get("gameUiConfig") if isinstance(project.get("gameUiConfig"), dict) else {}
    for field_name, label in GAME_UI_ASSET_REFERENCE_LABELS.items():
        asset_id = str(game_ui_config.get(field_name) or "").strip()
        if not asset_id:
            continue
        asset = assets_by_id.get(asset_id)
        check_path = f"gameUiConfig.{field_name}"
        if not asset:
            add_release_check_issue(
                issues,
                "warning",
                "game_ui_asset_reference_missing",
                f"成品 UI 皮肤引用了不存在的素材：{label} ({asset_id})",
                "重新选择这个 UI 素材，或清空该绑定；Runtime 会回退到基础 UI，但自定义皮肤不会完整显示。",
                check_path,
            )
            continue
        export_url = str(asset.get("exportUrl") or "").strip()
        if asset.get("isMissing") or not export_url or not (bundle_dir / export_url).is_file():
            add_release_check_issue(
                issues,
                "warning",
                "game_ui_asset_file_missing",
                f"成品 UI 皮肤素材不可用：{label}",
                "回到素材库重新导入或替换该 UI 素材，再重新导出原生 Runtime 包。",
                export_url or check_path,
            )
        if str(asset.get("type") or "") not in ASSET_TYPE_IMAGE:
            add_release_check_issue(
                issues,
                "warning",
                "game_ui_asset_type_risk",
                f"成品 UI 皮肤绑定的不是图片素材：{label}",
                "九宫格、Logo 和 UI 叠层建议使用 ui/background/cg/sprite 类型图片。",
                export_url or check_path,
            )

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_name = str(asset.get("name") or asset.get("id") or "未命名素材")
        asset_type = str(asset.get("type") or "misc")
        export_url = str(asset.get("exportUrl") or "").strip()
        if asset.get("isMissing"):
            add_release_check_issue(
                issues,
                "error",
                "asset_marked_missing",
                f"素材缺失：{asset_name}",
                "回到素材库重新绑定文件，或删除未使用的缺失素材后重新导出。",
                export_url or asset_name,
            )
            continue
        if not export_url:
            continue
        asset_path = bundle_dir / export_url
        if not asset_path.is_file():
            add_release_check_issue(
                issues,
                "error",
                "asset_file_missing",
                f"导出资源不存在：{export_url}",
                "重新导出，或检查压缩包解压后是否遗漏 assets 目录。",
                export_url,
            )
            continue
        extension = asset_path.suffix.lower()
        file_size = asset_path.stat().st_size
        if asset_type in ASSET_TYPE_IMAGE and extension not in SUPPORTED_IMAGE_EXTENSIONS:
            add_release_check_issue(
                issues,
                "warning",
                "image_extension_risk",
                f"图片素材格式可能不稳定：{asset_name} ({extension or '无扩展名'})",
                "建议使用 png、jpg、jpeg、bmp 或 webp。",
                export_url,
            )
        if asset_type in {"bgm", "sfx", "voice", "audio"} and extension not in SUPPORTED_AUDIO_EXTENSIONS:
            add_release_check_issue(
                issues,
                "warning",
                "audio_extension_risk",
                f"音频素材格式可能不稳定：{asset_name} ({extension or '无扩展名'})",
                "建议使用 ogg、wav 或 mp3，并在目标系统实机听一遍。",
                export_url,
            )
        if asset_type == "video":
            if extension not in SUPPORTED_VIDEO_EXTENSIONS:
                add_release_check_issue(
                    issues,
                    "warning",
                    "video_extension_risk",
                    f"视频素材格式可能不稳定：{asset_name} ({extension or '无扩展名'})",
                    "建议使用 mp4、webm、mov 或 m4v，并在目标系统实机播放一次。",
                    export_url,
                )
            video_bridge_available = can_open_external_video()
            optional_video_hint = (
                f"如需检查可选窗口内帧预览，可运行 python runtime_player.py --probe-video-preview .，"
                f"或安装 {NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME}。"
            )
            add_release_check_issue(
                issues,
                "warning",
                "video_native_external_player_bridge"
                if video_bridge_available
                else "video_native_external_player_missing",
                f"原生 Runtime 会用系统播放器桥接视频素材：{asset_name}",
                (
                    f"运行到视频卡时可按 V 调用{get_external_video_opener_label()}播放；"
                    "这不是内嵌解码，正式发布前仍建议在目标系统实机确认 OP/ED/PV。"
                    + optional_video_hint
                    if video_bridge_available
                    else "当前系统没有检测到可用的视频打开器；网页包和 NW.js 桌面包仍可直接播放视频。"
                    + optional_video_hint
                ),
                export_url,
            )
            if file_size > LARGE_VIDEO_WARNING_BYTES:
                add_release_check_issue(
                    issues,
                    "warning",
                    "large_video_asset",
                    f"视频素材偏大：{asset_name} ({file_size // 1024 // 1024} MB)",
                    "建议压缩码率或提供较短 OP/ED 版本，避免 Preview 包体过大。",
                    export_url,
                )
        if asset_type in ASSET_TYPE_IMAGE and file_size > LARGE_IMAGE_WARNING_BYTES:
            add_release_check_issue(
                issues,
                "warning",
                "large_image_asset",
                f"图片素材偏大：{asset_name} ({file_size // 1024 // 1024} MB)",
                "建议压缩或降低分辨率，避免低配机器切场景卡顿。",
                export_url,
            )
        if asset_type in {"bgm", "sfx", "voice", "audio"} and file_size > LARGE_AUDIO_WARNING_BYTES:
            add_release_check_issue(
                issues,
                "warning",
                "large_audio_asset",
                f"音频素材偏大：{asset_name} ({file_size // 1024 // 1024} MB)",
                "建议转成 ogg 或压缩码率，降低发布包体积。",
                export_url,
            )

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    return {
        "status": get_release_check_status(issues),
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "projectTitle": project_title,
        "summary": {
            "errors": error_count,
            "warnings": warning_count,
            "assetCount": len(assets),
            "sceneCount": len(scenes),
            "formalSaveSlotCount": formal_slot_count,
        },
        "issues": issues,
    }


def print_release_check_report(bundle_dir: Path) -> None:
    report = build_release_check_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def collect_video_block_usages(chapters: list[dict]) -> dict[str, list[dict]]:
    usages: dict[str, list[dict]] = {}
    for chapter in chapters:
        chapter_name = str(chapter.get("name") or chapter.get("chapterId") or "未命名章节")
        for scene in chapter.get("scenes") or []:
            scene_id = str(scene.get("id") or "")
            scene_name = str(scene.get("name") or scene_id or "未命名场景")
            for block_index, block in enumerate(scene.get("blocks") or []):
                if str(block.get("type") or "").strip() != "video_play":
                    continue
                asset_id = str(block.get("assetId") or "").strip()
                if not asset_id:
                    continue
                usages.setdefault(asset_id, []).append(
                    {
                        "chapterName": chapter_name,
                        "sceneId": scene_id,
                        "sceneName": scene_name,
                        "blockIndex": block_index,
                        "title": str(block.get("title") or "视频播放"),
                        "startTimeSeconds": block.get("startTimeSeconds"),
                        "endTimeSeconds": block.get("endTimeSeconds"),
                        "skippable": bool(block.get("skippable", True)),
                    }
                )
    return usages


def build_native_video_bridge_report(bundle_dir: Path) -> dict:
    data_path = bundle_dir / DEFAULT_GAME_DATA_NAME
    payload = load_game_data(data_path)
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    video_usages = collect_video_block_usages(chapters)
    opener_available = can_open_external_video()
    entries = []
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("type") != "video":
            continue
        asset_id = str(asset.get("id") or "")
        export_url = str(asset.get("exportUrl") or "").strip()
        asset_path = bundle_dir / export_url if export_url else None
        extension = asset_path.suffix.lower() if asset_path else ""
        exists = bool(asset_path and asset_path.is_file())
        entries.append(
            {
                "assetId": asset_id,
                "name": str(asset.get("name") or asset_id or "未命名视频"),
                "exportUrl": export_url,
                "exists": exists,
                "extension": extension,
                "extensionSupported": extension in SUPPORTED_VIDEO_EXTENSIONS,
                "externalPlaybackMode": "system_player_bridge",
                "nativePreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
                "openerAvailable": opener_available,
                "openerLabel": get_external_video_opener_label() if opener_available else "",
                "usages": video_usages.get(asset_id, []),
            }
        )
    return {
        "status": "ready" if entries and opener_available else ("no_video" if not entries else "needs_system_opener"),
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "summary": {
            "videoAssetCount": len(entries),
            "videoBlockCount": sum(len(entry["usages"]) for entry in entries),
            "openerAvailable": opener_available,
        },
        "nativePreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
        "backendOptions": get_native_video_backend_options(bundle_dir),
        "entries": entries,
    }


def print_native_video_bridge_report(bundle_dir: Path) -> None:
    report = build_native_video_bridge_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_native_video_backend_report(bundle_dir: Path) -> dict:
    bridge_report = build_native_video_bridge_report(bundle_dir)
    backend_options = bridge_report.get("backendOptions") or get_native_video_backend_options(bundle_dir)
    embedded_candidates = [
        option
        for option in backend_options
        if option.get("embeddedVideo")
    ]
    available_embedded = [option for option in embedded_candidates if option.get("available")]
    bridge_status = bridge_report.get("status")
    if bridge_status == "no_video":
        recommendation = "当前导出包没有视频素材；如果后续加入 OP/ED/PV，可以继续使用系统播放器桥接。"
    elif bridge_status == "ready":
        recommendation = "当前可以继续使用系统播放器桥接。"
    else:
        recommendation = "当前系统没有检测到可用外部视频打开器，建议优先发布网页/NW.js 包或在目标系统安装默认视频播放器。"
    if available_embedded:
        recommendation += " 已检测到可选内嵌画面后端，可用于后续实验性窗口内视频帧预览。"
    else:
        recommendation += f" 如需尝试实验性内嵌画面后端，可安装 {NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME}。"
    return {
        "status": (
            "no_video"
            if bridge_status == "no_video"
            else ("embedded_candidate_available" if available_embedded else "bridge_only")
        ),
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "nativePreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
        "videoAssetCount": (bridge_report.get("summary") or {}).get("videoAssetCount", 0),
        "videoBlockCount": (bridge_report.get("summary") or {}).get("videoBlockCount", 0),
        "recommendation": recommendation,
        "backendOptions": backend_options,
        "previewProbeCommand": "python runtime_player.py --probe-video-preview .",
    }


def print_native_video_backend_report(bundle_dir: Path) -> None:
    report = build_native_video_backend_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_video_preview_probe_entry_without_attempt(entry: dict, status: str, message: str) -> dict:
    usage = (entry.get("usages") or [{}])[0] or {}
    return {
        "assetId": entry.get("assetId"),
        "name": entry.get("name"),
        "exportUrl": entry.get("exportUrl"),
        "exists": bool(entry.get("exists")),
        "startTimeSeconds": normalize_video_time_seconds(usage.get("startTimeSeconds")),
        "attempted": False,
        "status": status,
        "message": message,
        "surfaceSize": None,
    }


def build_native_video_preview_probe_report(
    bundle_dir: Path,
    pygame_module=None,
    cv2_module=None,
    max_assets: int = 3,
) -> dict:
    bridge_report = build_native_video_bridge_report(bundle_dir)
    entries = bridge_report.get("entries") or []
    backend_options = bridge_report.get("backendOptions") or get_native_video_backend_options(bundle_dir)
    base_report = {
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "nativePreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
        "backendId": "opencv_frame_preview",
        "backendOptions": backend_options,
        "bridgeStatus": bridge_report.get("status"),
        "summary": {
            "videoAssetCount": len(entries),
            "probedCount": 0,
            "successCount": 0,
            "failedCount": 0,
        },
        "entries": [],
    }
    if not entries:
        return {
            **base_report,
            "status": "no_video",
            "recommendation": "当前导出包没有视频素材，不需要检查视频帧预览。",
        }

    cv2_available = cv2_module is not None or is_optional_python_module_available("cv2")
    if not cv2_available:
        return {
            **base_report,
            "status": "optional_dependency_missing",
            "recommendation": f"未安装 {NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME}，视频卡片会使用影院式桥接卡；需要帧预览时再安装可选依赖。",
            "entries": [
                build_video_preview_probe_entry_without_attempt(entry, "optional_dependency_missing", "未安装 OpenCV：使用桥接卡")
                for entry in entries[:max_assets]
            ],
        }

    if pygame_module is None:
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        pygame_module = import_optional_python_module("pygame")
    if pygame_module is None:
        return {
            **base_report,
            "status": "pygame_missing",
            "recommendation": "已检测到 OpenCV，但当前 Python 环境缺少 pygame-ce，无法生成 Runtime 预览 Surface。",
            "entries": [
                build_video_preview_probe_entry_without_attempt(entry, "pygame_missing", "缺少 pygame-ce：无法生成预览 Surface")
                for entry in entries[:max_assets]
            ],
        }

    should_quit_pygame = False
    if hasattr(pygame_module, "get_init") and hasattr(pygame_module, "init") and not pygame_module.get_init():
        pygame_module.init()
        should_quit_pygame = True

    probe_entries = []
    try:
        for entry in entries[:max_assets]:
            usage = (entry.get("usages") or [{}])[0] or {}
            start_time = normalize_video_time_seconds(usage.get("startTimeSeconds"))
            export_url = str(entry.get("exportUrl") or "").strip()
            asset_path = bundle_dir / export_url if export_url else None
            if not asset_path or not asset_path.is_file():
                probe_entries.append(
                    {
                        "assetId": entry.get("assetId"),
                        "name": entry.get("name"),
                        "exportUrl": export_url,
                        "exists": False,
                        "startTimeSeconds": start_time,
                        "attempted": False,
                        "status": "file_missing",
                        "message": "视频文件不存在",
                        "surfaceSize": None,
                    }
                )
                continue

            surface, message = load_opencv_video_frame_surface(
                pygame_module,
                asset_path,
                start_time,
                cv2_module=cv2_module,
            )
            surface_size = None
            if surface is not None:
                width, height = surface.get_size()
                surface_size = {"width": int(width), "height": int(height)}
            probe_entries.append(
                {
                    "assetId": entry.get("assetId"),
                    "name": entry.get("name"),
                    "exportUrl": export_url,
                    "exists": True,
                    "startTimeSeconds": start_time,
                    "attempted": True,
                    "status": "ready" if surface is not None else "frame_unavailable",
                    "message": message,
                    "surfaceSize": surface_size,
                }
            )
    finally:
        if should_quit_pygame and hasattr(pygame_module, "quit"):
            pygame_module.quit()

    success_count = sum(1 for entry in probe_entries if entry.get("status") == "ready")
    failed_count = sum(1 for entry in probe_entries if entry.get("status") != "ready")
    if success_count and failed_count:
        status = "partial"
        recommendation = "部分视频可以生成帧预览；失败的视频仍会自动回落到系统播放器桥接卡。"
    elif success_count:
        status = "ready"
        recommendation = "OpenCV 帧预览探针通过；视频卡片可显示剪辑起点附近的画面帧。"
    else:
        status = "all_failed"
        recommendation = "OpenCV 已可用，但没有视频成功生成帧预览；请检查编码格式，或继续使用系统播放器桥接。"

    return {
        **base_report,
        "status": status,
        "recommendation": recommendation,
        "summary": {
            "videoAssetCount": len(entries),
            "probedCount": len(probe_entries),
            "successCount": success_count,
            "failedCount": failed_count,
        },
        "entries": probe_entries,
    }


def print_native_video_preview_probe_report(bundle_dir: Path) -> None:
    report = build_native_video_preview_probe_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_native_title_screen_report(bundle_dir: Path) -> dict:
    payload = load_game_data(bundle_dir / DEFAULT_GAME_DATA_NAME)
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    project_id = str(project.get("projectId") or "untitled_project")
    formal_slot_count = get_project_formal_save_slot_count(project)
    save_store = load_project_save_store(project_id, formal_slot_count)
    formal_slots = save_store.get("formalSlots") or []
    filled_formal_count = sum(1 for item in formal_slots if item)
    title_logo_asset_id = str((project.get("gameUiConfig") or {}).get("titleLogoAssetId") or "").strip()
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    assets_by_id = {str(asset.get("id")): asset for asset in assets if isinstance(asset, dict) and asset.get("id")}
    title_logo_asset = assets_by_id.get(title_logo_asset_id) if title_logo_asset_id else None
    title_logo_path = get_asset_runtime_path(bundle_dir, title_logo_asset)
    brand_logo_path = bundle_dir / ENGINE_BRAND_LOGO_RELATIVE_PATH
    auto_resume = load_project_auto_resume(project_id)
    return {
        "status": "ready",
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "projectTitle": str(project.get("title") or project.get("name") or "Tony Na Engine"),
        "titleLogoAssetId": title_logo_asset_id,
        "titleLogoExists": bool(title_logo_path and title_logo_path.is_file()),
        "engineBrandLogo": ENGINE_BRAND_LOGO_RELATIVE_PATH,
        "engineBrandLogoExists": brand_logo_path.is_file(),
        "formalSaveSlotCount": formal_slot_count,
        "filledFormalSaveCount": filled_formal_count,
        "hasAutoResume": auto_resume is not None,
        "menuItems": [
            {
                "key": key,
                "label": label,
                "enabled": key != "resume" or auto_resume is not None,
            }
            for key, label in TITLE_MENU_ITEMS
        ],
    }


def print_native_title_screen_report(bundle_dir: Path) -> None:
    report = build_native_title_screen_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def iter_export_scenes(chapters: list[dict]) -> list[dict]:
    return [scene for chapter in chapters for scene in (chapter.get("scenes") or [])]


def collect_scene_outgoing_targets(scene: dict | None) -> list[str]:
    if not scene:
        return []
    targets = []
    for block in scene.get("blocks", []) or []:
        block_type = str(block.get("type") or "").strip()
        if block_type == "jump":
            target = str(block.get("targetSceneId") or "").strip()
            if target:
                targets.append(target)
        elif block_type == "choice":
            for option in block.get("options", []) or []:
                target = str(option.get("gotoSceneId") or "").strip()
                if target:
                    targets.append(target)
        elif block_type == "condition":
            for branch in block.get("branches", []) or []:
                target = str(branch.get("gotoSceneId") or "").strip()
                if target:
                    targets.append(target)
            fallback = str(block.get("elseGotoSceneId") or "").strip()
            if fallback:
                targets.append(fallback)
    deduped = []
    for target in targets:
        if target not in deduped:
            deduped.append(target)
    return deduped


def build_ending_scene_ids(chapters: list[dict]) -> list[str]:
    scene_ids = []
    for scene in iter_export_scenes(chapters):
        scene_id = str(scene.get("id") or "").strip()
        if scene_id and not collect_scene_outgoing_targets(scene):
            scene_ids.append(scene_id)
    return scene_ids


def build_narration_archive_entry_id(scene_id: str | None, block_id: str | None, block_index: int) -> str:
    safe_scene_id = str(scene_id or "scene").strip() or "scene"
    safe_block_id = str(block_id or "block").strip() or "block"
    return f"{safe_scene_id}:{safe_block_id}:{max(0, int(block_index))}"


def build_relationship_archive_id(left_character_id: str | None, right_character_id: str | None) -> str:
    pair = sorted(
        [
            str(left_character_id or "").strip(),
            str(right_character_id or "").strip(),
        ]
    )
    return "__".join(item for item in pair if item)


def build_voice_replay_entry_id(scene_id: str | None, block_id: str | None, block_index: int) -> str:
    return build_narration_archive_entry_id(scene_id, block_id, block_index)


def mix_rgb(color_a: tuple[int, int, int], color_b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    ratio = clamp(float(amount), 0.0, 1.0)
    return tuple(
        int(round(channel_a + (channel_b - channel_a) * ratio))
        for channel_a, channel_b in zip(color_a, color_b)
    )


def hex_to_rgb(value: str | None, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return tuple(clamp_int(channel, 0, 255, fallback[index]) for index, channel in enumerate(value[:3]))
        except Exception:
            return fallback
    safe_value = str(value or "").strip().lstrip("#")
    if len(safe_value) != 6:
        return fallback
    try:
        return tuple(int(safe_value[index : index + 2], 16) for index in range(0, 6, 2))
    except Exception:
        return fallback


def get_safe_native_particle_preset(preset: str | None) -> str:
    safe_preset = str(preset or "").strip()
    return safe_preset if safe_preset in NATIVE_PARTICLE_PRESET_DEFAULTS else "snow"


def get_safe_option(value, allowed: set[str], fallback: str) -> str:
    safe_value = str(value or "").strip()
    return safe_value if safe_value in allowed else fallback


def get_effect_duration_seconds(value) -> float:
    return EFFECT_DURATION_SECONDS.get(get_safe_option(value, set(EFFECT_DURATION_SECONDS), "medium"), EFFECT_DURATION_SECONDS["medium"])


def normalize_native_visual_effect_block(block: dict | None) -> dict:
    block = block or {}
    block_type = str(block.get("type") or "").strip()
    if block_type == "screen_shake":
        return {
            "type": block_type,
            "intensity": get_safe_option(block.get("intensity"), set(SHAKE_DISTANCE), "medium"),
            "duration": get_safe_option(block.get("duration"), set(EFFECT_DURATION_SECONDS), "medium"),
        }
    if block_type == "screen_flash":
        return {
            "type": block_type,
            "color": get_safe_option(block.get("color"), set(FLASH_COLORS), "white"),
            "intensity": get_safe_option(block.get("intensity"), set(FLASH_ALPHA), "medium"),
            "duration": get_safe_option(block.get("duration"), set(EFFECT_DURATION_SECONDS), "medium"),
        }
    if block_type == "screen_fade":
        return {
            "type": block_type,
            "action": get_safe_option(block.get("action"), {"fade_out", "fade_in"}, "fade_out"),
            "color": get_safe_option(block.get("color"), set(FADE_COLORS), "black"),
            "duration": get_safe_option(block.get("duration"), set(EFFECT_DURATION_SECONDS), "medium"),
        }
    if block_type == "camera_zoom":
        return {
            "type": block_type,
            "action": get_safe_option(block.get("action"), {"zoom_in", "zoom_out", "reset"}, "zoom_in"),
            "strength": get_safe_option(block.get("strength"), {"light", "medium", "heavy"}, "medium"),
            "focus": get_safe_option(block.get("focus"), {"left", "center", "right"}, "center"),
        }
    if block_type == "camera_pan":
        return {
            "type": block_type,
            "target": get_safe_option(block.get("target"), {"left", "center", "right"}, "center"),
            "strength": get_safe_option(block.get("strength"), {"light", "medium", "heavy"}, "medium"),
        }
    if block_type == "screen_filter":
        return {
            "type": block_type,
            "action": get_safe_option(block.get("action"), {"apply", "clear"}, "apply"),
            "preset": get_safe_option(block.get("preset"), set(SCREEN_FILTER_WASH), "memory"),
            "strength": get_safe_option(block.get("strength"), {"soft", "medium", "strong"}, "medium"),
        }
    if block_type == "depth_blur":
        return {
            "type": block_type,
            "action": get_safe_option(block.get("action"), {"apply", "clear"}, "apply"),
            "focus": get_safe_option(block.get("focus"), {"left", "center", "right", "full"}, "full"),
            "strength": get_safe_option(block.get("strength"), set(DEPTH_BLUR_ALPHA), "medium"),
        }
    return {"type": block_type}


def normalize_native_particle_effect_config(effect: dict | None) -> dict:
    effect = effect or {}
    preset = get_safe_native_particle_preset(effect.get("preset"))
    defaults = NATIVE_PARTICLE_PRESET_DEFAULTS[preset]
    intensity = str(effect.get("intensity") or "medium").strip()
    if intensity not in NATIVE_PARTICLE_INTENSITY_MULTIPLIER:
        intensity = "medium"
    speed = str(effect.get("speed") or "medium").strip()
    if speed not in NATIVE_PARTICLE_SPEED_MULTIPLIER:
        speed = "medium"
    wind = str(effect.get("wind") or "still").strip()
    if wind not in NATIVE_PARTICLE_WIND_VALUE:
        wind = "still"
    area = str(effect.get("area") or "full").strip()
    if area not in NATIVE_PARTICLE_AREA_RANGES:
        area = "full"
    density = int(round(float(effect.get("density") or defaults["density"])))
    density = max(4, min(240, density))
    size_min = float(effect.get("sizeMin") or defaults["sizeMin"])
    size_max = float(effect.get("sizeMax") or defaults["sizeMax"])
    speed_value = float(effect.get("gravityY") or defaults["speed"])
    drift_value = float(effect.get("spreadX") or defaults["drift"])
    return {
        "action": str(effect.get("action") or "start").strip(),
        "preset": preset,
        "assetId": str(effect.get("assetId") or "").strip(),
        "intensity": intensity,
        "speed": speed,
        "wind": wind,
        "area": area,
        "density": density,
        "sizeMin": max(1.0, min(size_min, size_max)),
        "sizeMax": max(1.0, max(size_min, size_max)),
        "speedValue": speed_value,
        "driftValue": drift_value,
        "color": hex_to_rgb(effect.get("color"), defaults["color"]),
        "accentColor": hex_to_rgb(effect.get("colorAccent"), defaults["accent"]),
        "shape": defaults["shape"],
    }


def build_native_particle_item(config: dict, width: int, height: int) -> dict:
    size = random.uniform(float(config.get("sizeMin") or 4), float(config.get("sizeMax") or 10))
    area_start, area_end = NATIVE_PARTICLE_AREA_RANGES.get(config.get("area"), NATIVE_PARTICLE_AREA_RANGES["full"])
    start_x = random.uniform(width * area_start, width * area_end)
    start_y = random.uniform(-height * 0.2, height * 0.1)
    wind_bias = NATIVE_PARTICLE_WIND_VALUE.get(config.get("wind"), 0)
    speed_multiplier = NATIVE_PARTICLE_SPEED_MULTIPLIER.get(config.get("speed"), 1.0)
    velocity_x = (random.uniform(-1.0, 1.0) * float(config.get("driftValue") or 12) * 0.25) + wind_bias
    base_speed = float(config.get("speedValue") or 90) * speed_multiplier
    velocity_y = base_speed + random.uniform(-0.25, 0.25) * base_speed
    preset = str(config.get("preset") or "snow")
    if preset in {"bubbles", "smoke", "flame", "stardust", "glyphs"}:
        start_y = random.uniform(height * 0.4, height * 0.95)
        velocity_y *= -0.55 if preset != "flame" else -0.82
    lifetime = random.uniform(3.0, 8.0)
    return {
        "x": start_x,
        "y": start_y,
        "vx": velocity_x,
        "vy": velocity_y,
        "size": size,
        "life": lifetime,
        "maxLife": lifetime,
        "spin": random.uniform(-120, 120),
        "rotation": random.uniform(0, 360),
        "colorMix": random.random(),
        "wobble": random.uniform(4.0, 20.0),
        "wobblePhase": random.uniform(0, math.pi * 2),
    }


def build_native_particle_items(config: dict, width: int, height: int) -> list[dict]:
    if str(config.get("action") or "start") == "stop":
        return []
    density = int(config.get("density") or 0)
    density = int(density * NATIVE_PARTICLE_INTENSITY_MULTIPLIER.get(config.get("intensity"), 1.0))
    density = max(4, min(180, density))
    return [build_native_particle_item(config, width, height) for _ in range(density)]


def exercise_particle_effect(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    chapters = payload.get("chapters") or []
    particle_block = None
    for chapter in chapters:
        for scene in chapter.get("scenes") or []:
            for block in scene.get("blocks") or []:
                if str(block.get("type") or "").strip() == "particle_effect":
                    particle_block = block
                    break
            if particle_block:
                break
        if particle_block:
            break
    if not particle_block:
        particle_block = {"type": "particle_effect", "action": "start", "preset": "snow", "intensity": "medium", "speed": "medium", "wind": "still", "area": "full"}

    config = normalize_native_particle_effect_config(particle_block)
    if config["action"] == "stop":
        raise NativeRuntimeError("粒子自检拿到的是 stop 配置，无法验证渲染生成。")
    items = build_native_particle_items(config, 1280, 720)
    if not items:
        raise NativeRuntimeError("粒子条目没有生成。")
    if len(items) < 4:
        raise NativeRuntimeError("粒子条目数量过少，未达到最小预期。")
    print(f"Native runtime particle validation passed: preset={config['preset']} items={len(items)}")


def exercise_visual_effects(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    supported_types = {"screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur"}
    normalized = []
    for chapter in payload.get("chapters") or []:
        for scene in chapter.get("scenes") or []:
            for block in scene.get("blocks") or []:
                if str(block.get("type") or "").strip() in supported_types:
                    normalized.append(normalize_native_visual_effect_block(block))
    if not normalized:
        normalized = [
            normalize_native_visual_effect_block({"type": "screen_flash", "color": "white", "intensity": "soft", "duration": "short"}),
            normalize_native_visual_effect_block({"type": "camera_zoom", "action": "zoom_in", "strength": "light", "focus": "center"}),
            normalize_native_visual_effect_block({"type": "screen_filter", "action": "apply", "preset": "memory", "strength": "soft"}),
        ]
    if any(not item.get("type") for item in normalized):
        raise NativeRuntimeError("高级演出配置规范化失败。")
    print(f"Native runtime visual effects validation passed: {len(normalized)} blocks")


def exercise_player_profile(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    project_id = str(project.get("projectId") or "untitled_project")
    chapters = payload.get("chapters") or []
    scene = next((scene for chapter in chapters for scene in (chapter.get("scenes") or []) if scene.get("id")), None)
    if not scene:
        raise NativeRuntimeError("没有可用于测试续玩记录的场景。")

    profile = sanitize_player_profile(
        {
            "firstPlayedAt": now_iso(),
            "lastPlayedAt": now_iso(),
            "lastEndedAt": now_iso(),
            "totalPlayMs": 3210,
            "sessionCount": 2,
            "resumedCount": 1,
            "returnToTitleCount": 1,
        }
    )
    profile_path = write_project_player_profile(project_id, profile)
    loaded_profile = load_project_player_profile(project_id)
    if loaded_profile["sessionCount"] != 2 or loaded_profile["resumedCount"] != 1:
        raise NativeRuntimeError("玩家档案写入后没有正确读回。")

    snapshot = {
        "kind": "auto-resume",
        "savedAt": now_iso(),
        "sceneId": scene.get("id"),
        "sceneName": scene.get("name") or scene.get("id"),
        "blockIndex": 0,
        "variableState": {},
        "stageBackgroundAssetId": None,
        "visibleCharacters": {},
        "currentBgmAssetId": None,
        "finished": False,
        "finishedMessage": "",
        "summaryText": "Native runtime profile self test",
    }
    auto_resume_path = write_project_auto_resume(project_id, snapshot)
    loaded_snapshot = load_project_auto_resume(project_id)
    if not loaded_snapshot or loaded_snapshot.get("sceneId") != scene.get("id"):
        raise NativeRuntimeError("续玩记录写入后没有正确读回。")
    clear_project_auto_resume(project_id)
    if load_project_auto_resume(project_id) is not None:
        raise NativeRuntimeError("续玩记录清除后仍然存在。")
    print(f"Native runtime profile validation passed: profile={profile_path} autoResume={auto_resume_path}")


def exercise_save_load(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    formal_slot_count = get_project_formal_save_slot_count(project)
    chapters = payload.get("chapters") or []
    scenes = [scene for chapter in chapters for scene in (chapter.get("scenes") or [])]
    if not scenes:
        raise NativeRuntimeError("没有可用于测试存档的场景。")

    scene = scenes[0]
    snapshot = {
        "kind": "formal",
        "savedAt": now_iso(),
        "sceneId": scene.get("id"),
        "sceneName": scene.get("name") or scene.get("id"),
        "blockIndex": 0,
        "variableState": {
            variable.get("id"): variable.get("defaultValue")
            for variable in (payload.get("variables") or {}).get("variables", [])
            if variable.get("id")
        },
        "stageBackgroundAssetId": None,
        "visibleCharacters": {},
        "currentBgmAssetId": None,
        "finished": False,
        "finishedMessage": "",
        "summaryText": "Native runtime save-load self test",
    }

    project_id = str(project.get("projectId") or "untitled_project")
    store = {"quickSave": snapshot, "formalSlots": [snapshot] + [None] * (formal_slot_count - 1)}
    save_path = write_project_save_store(project_id, store)
    loaded = load_project_save_store(project_id, formal_slot_count)
    if loaded.get("quickSave", {}).get("sceneId") != scene.get("id"):
        raise NativeRuntimeError("快速存档写入后没有正确读回。")
    if (loaded.get("formalSlots") or [None])[0].get("sceneId") != scene.get("id"):
        raise NativeRuntimeError("正式存档写入后没有正确读回。")
    print(f"Native runtime save/load validation passed: {save_path}")


def describe_save_dialog(bundle_dir: Path, page: int = 0) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    save_store = load_project_save_store(
        str(project.get("projectId") or "untitled_project"),
        get_project_formal_save_slot_count(project),
    )
    summary = build_save_dialog_page_data(project, save_store, page=page)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def exercise_runtime_settings(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    project_id = str(project.get("projectId") or "untitled_project")
    write_project_runtime_settings(
        project_id,
        {
            "themeMode": "dark",
            "displayMode": "fullscreen",
            "textSpeed": "fast",
            "masterVolume": 78,
            "bgmVolume": 65,
            "sfxVolume": 70,
            "voiceVolume": 88,
        },
    )
    loaded = load_project_runtime_settings(project_id)
    if loaded["themeMode"] != "dark" or loaded["displayMode"] != "fullscreen" or loaded["textSpeed"] != "fast":
        raise NativeRuntimeError("原生 Runtime 设置写入后没有正确读回。")
    if loaded["masterVolume"] != 78 or loaded["voiceVolume"] != 88:
        raise NativeRuntimeError("原生 Runtime 音量设置读回不正确。")
    print(f"Native runtime settings validation passed: {get_project_settings_file_path(project_id)}")


def exercise_archive_progress(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    project_id = str(project.get("projectId") or "untitled_project")
    chapters = payload.get("chapters") or []
    assets = (payload.get("assets") or {}).get("assets") or []
    first_chapter_id = str((chapters[0] or {}).get("chapterId") or "")
    bgm_asset_id = next((str(asset.get("id")) for asset in assets if asset.get("type") == "bgm" and asset.get("id")), "")
    cg_asset_id = next((str(asset.get("id")) for asset in assets if asset.get("type") == "cg" and asset.get("id")), "")
    location_asset_id = next((str(asset.get("id")) for asset in assets if asset.get("type") == "background" and asset.get("id")), "")
    characters = (payload.get("characters") or {}).get("characters") or []
    character_id = next((str(character.get("id")) for character in characters if character.get("id")), "")
    valid_character_ids = {str(character.get("id")) for character in characters if character.get("id")}
    ending_scene_id = next((scene_id for scene_id in build_ending_scene_ids(chapters) if scene_id), "")
    narration_id = ""
    voice_replay_id = ""
    relation_id = ""
    for chapter in chapters:
        for scene in chapter.get("scenes") or []:
            encountered_character_ids: list[str] = []
            seen_character_ids: set[str] = set()
            for block_index, block in enumerate(scene.get("blocks") or []):
                speaker_id = str(block.get("speakerId") or "").strip()
                character_ref = str(block.get("characterId") or "").strip()
                for candidate in (speaker_id, character_ref):
                    if candidate and candidate in valid_character_ids and candidate not in seen_character_ids:
                        seen_character_ids.add(candidate)
                        encountered_character_ids.append(candidate)
                if not narration_id and str(block.get("type") or "").strip() == "narration":
                    narration_id = build_narration_archive_entry_id(scene.get("id"), block.get("id"), block_index)
                if not voice_replay_id and block.get("voiceAssetId"):
                    voice_replay_id = build_voice_replay_entry_id(scene.get("id"), block.get("id"), block_index)
                if not relation_id and len(encountered_character_ids) >= 2:
                    relation_id = build_relationship_archive_id(encountered_character_ids[0], encountered_character_ids[1])
            if narration_id and voice_replay_id and relation_id:
                break
        if narration_id and voice_replay_id and relation_id:
            break
    progress = {
        "chapterReplayUnlocked": [first_chapter_id] if first_chapter_id else [],
        "bgmUnlocked": [bgm_asset_id] if bgm_asset_id else [],
        "cgUnlocked": [cg_asset_id] if cg_asset_id else [],
        "locationUnlocked": [location_asset_id] if location_asset_id else [],
        "characterUnlocked": [character_id] if character_id else [],
        "narrationUnlocked": [narration_id] if narration_id else [],
        "relationUnlocked": [relation_id] if relation_id else [],
        "voiceReplayUnlocked": [voice_replay_id] if voice_replay_id else [],
        "endingUnlocked": [ending_scene_id] if ending_scene_id else [],
        "endingCompletionCount": 1 if ending_scene_id else 0,
        "endingLastCompletedAt": "2026-04-24T00:00:00+08:00" if ending_scene_id else None,
    }
    write_project_archive_progress(project_id, progress)
    loaded = load_project_archive_progress(project_id)
    if progress["chapterReplayUnlocked"] != loaded["chapterReplayUnlocked"]:
        raise NativeRuntimeError("章节回放进度写入后没有正确读回。")
    if progress["bgmUnlocked"] != loaded["bgmUnlocked"]:
        raise NativeRuntimeError("音乐鉴赏进度写入后没有正确读回。")
    if progress["cgUnlocked"] != loaded["cgUnlocked"]:
        raise NativeRuntimeError("CG 回想进度写入后没有正确读回。")
    if progress["locationUnlocked"] != loaded["locationUnlocked"]:
        raise NativeRuntimeError("地点图鉴进度写入后没有正确读回。")
    if progress["characterUnlocked"] != loaded["characterUnlocked"]:
        raise NativeRuntimeError("角色图鉴进度写入后没有正确读回。")
    if progress["narrationUnlocked"] != loaded["narrationUnlocked"]:
        raise NativeRuntimeError("旁白摘录进度写入后没有正确读回。")
    if progress["relationUnlocked"] != loaded["relationUnlocked"]:
        raise NativeRuntimeError("关系图鉴进度写入后没有正确读回。")
    if progress["voiceReplayUnlocked"] != loaded["voiceReplayUnlocked"]:
        raise NativeRuntimeError("语音回听进度写入后没有正确读回。")
    if progress["endingUnlocked"] != loaded["endingUnlocked"]:
        raise NativeRuntimeError("结局回放进度写入后没有正确读回。")
    if progress["endingCompletionCount"] != loaded["endingCompletionCount"]:
        raise NativeRuntimeError("结局完成次数写入后没有正确读回。")
    print(f"Native runtime archive progress validation passed: {get_project_progress_file_path(project_id)}")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def get_project_formal_save_slot_count(project: dict | None) -> int:
    runtime_settings = (project or {}).get("runtimeSettings") or {}
    try:
        value = int(runtime_settings.get("formalSaveSlotCount", DEFAULT_FORMAL_SAVE_SLOT_COUNT))
    except Exception:
        value = DEFAULT_FORMAL_SAVE_SLOT_COUNT
    return max(MIN_FORMAL_SAVE_SLOT_COUNT, min(MAX_FORMAL_SAVE_SLOT_COUNT, value))


def clamp_int(value, minimum: int, maximum: int, fallback: int) -> int:
    try:
        numeric = int(round(float(value)))
    except Exception:
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def parse_hex_color(value, fallback):
    safe_value = str(value or "").strip()
    if len(safe_value) == 7 and safe_value.startswith("#"):
        try:
            return tuple(int(safe_value[index:index + 2], 16) for index in (1, 3, 5))
        except Exception:
            return fallback
    return fallback


def get_safe_frame_slice(value, fallback: dict) -> dict:
    source = value if isinstance(value, dict) else {}
    return {
        "top": clamp_int(source.get("top"), 0, 96, int(fallback.get("top", 18))),
        "right": clamp_int(source.get("right"), 0, 96, int(fallback.get("right", 18))),
        "bottom": clamp_int(source.get("bottom"), 0, 96, int(fallback.get("bottom", 18))),
        "left": clamp_int(source.get("left"), 0, 96, int(fallback.get("left", 18))),
    }


def with_alpha(color, opacity_percent: int) -> tuple[int, int, int, int]:
    alpha = clamp_int(opacity_percent, 0, 100, 100)
    return (*color, int(round(alpha * 2.55)))


def normalize_video_time_seconds(value, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = fallback
    if not math.isfinite(numeric):
        numeric = fallback
    return max(0.0, numeric)


def format_video_timestamp(seconds: float | int | None) -> str:
    total_seconds = normalize_video_time_seconds(seconds)
    minutes = int(total_seconds // 60)
    seconds_remainder = total_seconds - minutes * 60
    if seconds_remainder.is_integer():
        return f"{minutes}:{int(seconds_remainder):02d}"
    return f"{minutes}:{seconds_remainder:04.1f}"


def build_video_clip_label(start_time: float, end_time: float) -> str:
    if start_time <= 0 and end_time <= 0:
        return "整段播放"
    return f"{format_video_timestamp(start_time)} -> {format_video_timestamp(end_time) if end_time > 0 else '结尾'}"


def get_safe_project_dialog_box_preset(value) -> str:
    return value if value == "custom" or value in DIALOG_BOX_PRESETS else DEFAULT_DIALOG_BOX_CONFIG["preset"]


def get_safe_project_dialog_box_shape(value) -> str:
    return value if value in {"rounded", "square", "capsule"} else DEFAULT_DIALOG_BOX_CONFIG["shape"]


def get_project_dialog_box_preset_config(preset) -> dict:
    safe_preset = get_safe_project_dialog_box_preset(preset)
    return {
        **DEFAULT_DIALOG_BOX_CONFIG,
        **(DIALOG_BOX_PRESETS.get(safe_preset) or {}),
        "preset": safe_preset,
    }


def get_project_dialog_box_config(project: dict | None) -> dict:
    source = (project or {}).get("dialogBoxConfig") or {}
    base = get_project_dialog_box_preset_config(source.get("preset"))
    return {
        **base,
        "preset": get_safe_project_dialog_box_preset(source.get("preset", base["preset"])),
        "shape": get_safe_project_dialog_box_shape(source.get("shape", base["shape"])),
        "widthPercent": clamp_int(source.get("widthPercent"), 55, 100, base["widthPercent"]),
        "minHeight": clamp_int(source.get("minHeight"), 96, 320, base["minHeight"]),
        "paddingX": clamp_int(source.get("paddingX"), 8, 72, base["paddingX"]),
        "paddingY": clamp_int(source.get("paddingY"), 6, 48, base["paddingY"]),
        "backgroundColor": parse_hex_color(source.get("backgroundColor"), parse_hex_color(base["backgroundColor"], COLOR_PANEL)),
        "backgroundOpacity": clamp_int(source.get("backgroundOpacity"), 0, 100, base["backgroundOpacity"]),
        "borderColor": parse_hex_color(source.get("borderColor"), parse_hex_color(base["borderColor"], COLOR_PANEL_BORDER)),
        "borderOpacity": clamp_int(source.get("borderOpacity"), 0, 100, base["borderOpacity"]),
        "textColor": parse_hex_color(source.get("textColor"), parse_hex_color(base["textColor"], COLOR_TEXT)),
        "speakerColor": parse_hex_color(source.get("speakerColor"), parse_hex_color(base["speakerColor"], COLOR_TEXT)),
        "hintColor": parse_hex_color(source.get("hintColor"), parse_hex_color(base["hintColor"], COLOR_TEXT_MUTED)),
        "blurStrength": clamp_int(source.get("blurStrength"), 0, 24, base["blurStrength"]),
        "borderWidth": clamp_int(source.get("borderWidth"), 0, 4, base["borderWidth"]),
        "shadowStrength": clamp_int(source.get("shadowStrength"), 0, 48, base["shadowStrength"]),
        "panelAssetId": str(source.get("panelAssetId") or "").strip(),
        "panelAssetOpacity": clamp_int(source.get("panelAssetOpacity"), 0, 100, base["panelAssetOpacity"]),
        "panelAssetFit": "contain" if source.get("panelAssetFit") == "contain" else "cover",
        "anchor": get_safe_option(
            source.get("anchor"),
            {"bottom", "center", "top", "free"},
            base["anchor"],
        ),
        "offsetXPercent": clamp_int(source.get("offsetXPercent"), -35, 35, base["offsetXPercent"]),
        "offsetYPercent": clamp_int(source.get("offsetYPercent"), -35, 35, base["offsetYPercent"]),
    }


def get_project_game_ui_config(project: dict | None) -> dict:
    source = (project or {}).get("gameUiConfig") or {}
    base = {**DEFAULT_GAME_UI_CONFIG}
    return {
        **base,
        "preset": get_safe_option(
            source.get("preset"),
            {"stellar", "warm", "paper", "minimal", "custom"},
            base["preset"],
        ),
        "layoutPreset": get_safe_option(
            source.get("layoutPreset"),
            {"balanced", "cinematic", "compact", "minimal", "custom"},
            base["layoutPreset"],
        ),
        "titleLayout": get_safe_option(
            source.get("titleLayout"),
            {"center", "left", "poster"},
            base["titleLayout"],
        ),
        "fontStyle": get_safe_option(source.get("fontStyle"), {"modern", "serif", "rounded"}, base["fontStyle"]),
        "surfaceStyle": get_safe_option(
            source.get("surfaceStyle"),
            {"glass", "solid", "minimal"},
            base["surfaceStyle"],
        ),
        "brandMode": get_safe_option(source.get("brandMode"), {"project", "engine", "hidden"}, base["brandMode"]),
        "sidePanelMode": get_safe_option(
            source.get("sidePanelMode"),
            {"full", "compact", "hidden"},
            base["sidePanelMode"],
        ),
        "sidePanelPosition": get_safe_option(
            source.get("sidePanelPosition"),
            {"right", "left"},
            base["sidePanelPosition"],
        ),
        "topbarPosition": get_safe_option(
            source.get("topbarPosition"),
            {"top", "bottom", "hidden"},
            base["topbarPosition"],
        ),
        "hudPosition": get_safe_option(
            source.get("hudPosition"),
            {"top", "top-left", "top-right", "bottom-left", "bottom-right", "hidden"},
            base["hudPosition"],
        ),
        "titleCardAnchor": get_safe_option(
            source.get("titleCardAnchor"),
            {"center", "left", "right", "top", "bottom", "free"},
            base["titleCardAnchor"],
        ),
        "titleCardOffsetXPercent": clamp_int(
            source.get("titleCardOffsetXPercent"),
            -35,
            35,
            base["titleCardOffsetXPercent"],
        ),
        "titleCardOffsetYPercent": clamp_int(
            source.get("titleCardOffsetYPercent"),
            -35,
            35,
            base["titleCardOffsetYPercent"],
        ),
        "layoutGap": clamp_int(source.get("layoutGap"), 8, 48, base["layoutGap"]),
        "sidePanelWidth": clamp_int(source.get("sidePanelWidth"), 240, 460, base["sidePanelWidth"]),
        "backgroundColor": parse_hex_color(source.get("backgroundColor"), parse_hex_color(base["backgroundColor"], COLOR_BG)),
        "backgroundAccentColor": parse_hex_color(
            source.get("backgroundAccentColor"),
            parse_hex_color(base["backgroundAccentColor"], COLOR_ACCENT),
        ),
        "panelColor": parse_hex_color(source.get("panelColor"), parse_hex_color(base["panelColor"], COLOR_PANEL)),
        "panelOpacity": clamp_int(source.get("panelOpacity"), 35, 100, base["panelOpacity"]),
        "textColor": parse_hex_color(source.get("textColor"), parse_hex_color(base["textColor"], COLOR_TEXT)),
        "mutedTextColor": parse_hex_color(
            source.get("mutedTextColor"),
            parse_hex_color(base["mutedTextColor"], COLOR_TEXT_MUTED),
        ),
        "accentColor": parse_hex_color(source.get("accentColor"), parse_hex_color(base["accentColor"], COLOR_ACCENT)),
        "accentAltColor": parse_hex_color(
            source.get("accentAltColor"),
            parse_hex_color(base["accentAltColor"], COLOR_ACCENT_ALT),
        ),
        "buttonTextColor": parse_hex_color(source.get("buttonTextColor"), parse_hex_color(base["buttonTextColor"], COLOR_TEXT)),
        "borderColor": parse_hex_color(source.get("borderColor"), parse_hex_color(base["borderColor"], COLOR_PANEL_BORDER)),
        "borderOpacity": clamp_int(source.get("borderOpacity"), 0, 100, base["borderOpacity"]),
        "cornerRadius": clamp_int(source.get("cornerRadius"), 4, 42, base["cornerRadius"]),
        "backdropBlur": clamp_int(source.get("backdropBlur"), 0, 28, base["backdropBlur"]),
        "stageVignette": clamp_int(source.get("stageVignette"), 0, 80, base["stageVignette"]),
        "motionIntensity": clamp_int(source.get("motionIntensity"), 0, 100, base["motionIntensity"]),
        "titleBackgroundAssetId": str(source.get("titleBackgroundAssetId") or "").strip(),
        "titleBackgroundFit": "contain" if source.get("titleBackgroundFit") == "contain" else "cover",
        "titleBackgroundOpacity": clamp_int(source.get("titleBackgroundOpacity"), 0, 100, base["titleBackgroundOpacity"]),
        "titleLogoAssetId": str(source.get("titleLogoAssetId") or "").strip(),
        "panelFrameAssetId": str(source.get("panelFrameAssetId") or "").strip(),
        "panelFrameOpacity": clamp_int(source.get("panelFrameOpacity"), 0, 100, base["panelFrameOpacity"]),
        "panelFrameSlice": get_safe_frame_slice(source.get("panelFrameSlice"), base["panelFrameSlice"]),
        "buttonFrameAssetId": str(source.get("buttonFrameAssetId") or "").strip(),
        "buttonHoverFrameAssetId": str(source.get("buttonHoverFrameAssetId") or "").strip(),
        "buttonPressedFrameAssetId": str(source.get("buttonPressedFrameAssetId") or "").strip(),
        "buttonDisabledFrameAssetId": str(source.get("buttonDisabledFrameAssetId") or "").strip(),
        "buttonFrameOpacity": clamp_int(source.get("buttonFrameOpacity"), 0, 100, base["buttonFrameOpacity"]),
        "buttonFrameSlice": get_safe_frame_slice(source.get("buttonFrameSlice"), base["buttonFrameSlice"]),
        "saveSlotFrameAssetId": str(source.get("saveSlotFrameAssetId") or "").strip(),
        "systemPanelFrameAssetId": str(source.get("systemPanelFrameAssetId") or "").strip(),
        "uiOverlayAssetId": str(source.get("uiOverlayAssetId") or "").strip(),
        "uiOverlayOpacity": clamp_int(source.get("uiOverlayOpacity"), 0, 100, base["uiOverlayOpacity"]),
    }


def get_runtime_save_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / SAVE_SUBDIR_NAME


def get_runtime_settings_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / SETTINGS_SUBDIR_NAME


def get_runtime_progress_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / PROGRESS_SUBDIR_NAME


def get_runtime_profile_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / PROFILE_SUBDIR_NAME


def get_runtime_auto_resume_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / AUTO_RESUME_SUBDIR_NAME


def get_runtime_log_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / LOG_SUBDIR_NAME


def write_runtime_crash_log(game_data_path: Path, error: BaseException, context: str) -> Path:
    log_dir = get_runtime_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    log_path = log_dir / f"runtime-crash-{timestamp}.log"
    lines = [
        "Tony Na Engine Native Runtime Crash Log",
        f"Time: {now_iso()}",
        f"Context: {context}",
        f"Game data: {game_data_path}",
        f"Python: {sys.version.replace(chr(10), ' ')}",
        f"Platform: {platform.platform()}",
        f"Frozen: {bool(getattr(sys, 'frozen', False))}",
        "",
        "Error:",
        f"{type(error).__name__}: {error}",
        "",
        "Traceback:",
        traceback.format_exc(),
        "",
    ]
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return log_path


def wrap_plain_text(text: str, max_chars: int) -> list[str]:
    safe_text = str(text or "")
    lines: list[str] = []
    for raw_line in safe_text.splitlines() or [""]:
        current = raw_line
        while len(current) > max_chars:
            lines.append(current[:max_chars])
            current = current[max_chars:]
        lines.append(current)
    return lines


def show_runtime_error_screen(pygame, message: str, log_path: Path | None) -> None:
    try:
        screen = pygame.display.get_surface()
        if screen is None:
            screen = pygame.display.set_mode((860, 360))
        pygame.display.set_caption("Tony Na Engine Runtime Error")
        font_title = pygame.font.SysFont("Arial", 26, bold=True)
        font_body = pygame.font.SysFont("Arial", 18)
        clock = pygame.time.Clock()
        details = str(log_path) if log_path else "未能写入日志"
        lines = [
            "原生 Runtime 没有成功启动",
            "",
            *wrap_plain_text(message, 54)[:4],
            "",
            "错误日志：",
            *wrap_plain_text(details, 62)[:3],
            "",
            "按 Esc / Return 关闭这个窗口。",
        ]
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    running = False
            screen.fill(COLOR_BG)
            y = 34
            screen.blit(font_title.render(lines[0], True, COLOR_WARNING), (38, y))
            y += 52
            for line in lines[2:]:
                color = COLOR_TEXT if line else COLOR_TEXT_MUTED
                screen.blit(font_body.render(line, True, color), (38, y))
                y += 26
            pygame.display.flip()
            clock.tick(30)
    except Exception:
        pass


def make_project_save_filename(project_id: str) -> str:
    clean = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in project_id)
    clean = clean.strip("_") or "untitled_project"
    return f"{clean}.json"


def get_project_save_file_path(project_id: str) -> Path:
    return get_runtime_save_dir() / make_project_save_filename(project_id)


def get_project_settings_file_path(project_id: str) -> Path:
    return get_runtime_settings_dir() / make_project_save_filename(project_id)


def get_project_progress_file_path(project_id: str) -> Path:
    return get_runtime_progress_dir() / make_project_save_filename(project_id)


def get_project_profile_file_path(project_id: str) -> Path:
    return get_runtime_profile_dir() / make_project_save_filename(project_id)


def get_project_auto_resume_file_path(project_id: str) -> Path:
    return get_runtime_auto_resume_dir() / make_project_save_filename(project_id)


def load_project_save_store(project_id: str, slot_count: int) -> dict:
    save_path = get_project_save_file_path(project_id)
    if not save_path.is_file():
        return {"quickSave": None, "formalSlots": [None] * slot_count}
    try:
        payload = json.loads(save_path.read_text(encoding="utf-8"))
    except Exception:
        return {"quickSave": None, "formalSlots": [None] * slot_count}

    formal_slots = payload.get("formalSlots")
    if not isinstance(formal_slots, list):
        formal_slots = [None] * slot_count
    formal_slots = list(formal_slots[:slot_count])
    while len(formal_slots) < slot_count:
        formal_slots.append(None)
    return {
        "quickSave": payload.get("quickSave"),
        "formalSlots": formal_slots,
    }


def sanitize_player_profile(value: dict | None) -> dict:
    source = value if isinstance(value, dict) else {}

    def clean_optional_time(raw_value):
        safe_value = str(raw_value or "").strip()
        return safe_value or None

    def clean_count(raw_value) -> int:
        try:
            return max(0, int(raw_value or 0))
        except Exception:
            return 0

    return {
        "firstPlayedAt": clean_optional_time(source.get("firstPlayedAt")),
        "lastPlayedAt": clean_optional_time(source.get("lastPlayedAt")),
        "lastEndedAt": clean_optional_time(source.get("lastEndedAt")),
        "totalPlayMs": clean_count(source.get("totalPlayMs")),
        "sessionCount": clean_count(source.get("sessionCount")),
        "resumedCount": clean_count(source.get("resumedCount")),
        "returnToTitleCount": clean_count(source.get("returnToTitleCount")),
    }


def load_project_player_profile(project_id: str) -> dict:
    profile_path = get_project_profile_file_path(project_id)
    if not profile_path.is_file():
        return sanitize_player_profile(DEFAULT_PLAYER_PROFILE)
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return sanitize_player_profile(DEFAULT_PLAYER_PROFILE)
    return sanitize_player_profile(payload)


def write_project_player_profile(project_id: str, profile: dict) -> Path:
    profile_dir = get_runtime_profile_dir()
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = get_project_profile_file_path(project_id)
    safe_profile = sanitize_player_profile(profile)
    profile_path.write_text(json.dumps(safe_profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return profile_path


def sanitize_auto_resume_snapshot(value: dict | None) -> dict | None:
    if not isinstance(value, dict):
        return None
    scene_id = str(value.get("sceneId") or "").strip()
    if not scene_id and not bool(value.get("finished")):
        return None
    snapshot = dict(value)
    snapshot["kind"] = str(snapshot.get("kind") or "auto-resume")
    snapshot["savedAt"] = str(snapshot.get("savedAt") or now_iso())
    snapshot["sceneId"] = scene_id
    snapshot["sceneName"] = str(snapshot.get("sceneName") or scene_id or "未命名场景")
    try:
        block_index = int(snapshot.get("blockIndex") or 0)
    except Exception:
        block_index = 0
    snapshot["blockIndex"] = max(0, block_index)
    snapshot["summaryText"] = str(snapshot.get("summaryText") or "").strip()
    snapshot["finished"] = bool(snapshot.get("finished"))
    snapshot["finishedMessage"] = str(snapshot.get("finishedMessage") or "")
    if not isinstance(snapshot.get("variableState"), dict):
        snapshot["variableState"] = {}
    if not isinstance(snapshot.get("visibleCharacters"), dict):
        snapshot["visibleCharacters"] = {}
    return snapshot


def load_project_auto_resume(project_id: str) -> dict | None:
    auto_resume_path = get_project_auto_resume_file_path(project_id)
    if not auto_resume_path.is_file():
        return None
    try:
        payload = json.loads(auto_resume_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return sanitize_auto_resume_snapshot(payload)


def write_project_auto_resume(project_id: str, snapshot: dict) -> Path:
    auto_resume_dir = get_runtime_auto_resume_dir()
    auto_resume_dir.mkdir(parents=True, exist_ok=True)
    auto_resume_path = get_project_auto_resume_file_path(project_id)
    safe_snapshot = sanitize_auto_resume_snapshot(snapshot)
    if safe_snapshot is None:
        safe_snapshot = {"kind": "auto-resume", "savedAt": now_iso(), "sceneId": "", "sceneName": "未命名场景", "blockIndex": 0}
    auto_resume_path.write_text(json.dumps(safe_snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return auto_resume_path


def clear_project_auto_resume(project_id: str) -> Path:
    auto_resume_path = get_project_auto_resume_file_path(project_id)
    try:
        auto_resume_path.unlink()
    except FileNotFoundError:
        pass
    return auto_resume_path


def sanitize_archive_progress(value: dict | None) -> dict:
    source = value or {}

    def clean_id_list(raw_value) -> list[str]:
        if not isinstance(raw_value, list):
            return []
        result = []
        for item in raw_value:
            safe_item = str(item or "").strip()
            if safe_item and safe_item not in result:
                result.append(safe_item)
        return result

    return {
        "chapterReplayUnlocked": clean_id_list(source.get("chapterReplayUnlocked")),
        "bgmUnlocked": clean_id_list(source.get("bgmUnlocked")),
        "cgUnlocked": clean_id_list(source.get("cgUnlocked")),
        "locationUnlocked": clean_id_list(source.get("locationUnlocked")),
        "characterUnlocked": clean_id_list(source.get("characterUnlocked")),
        "narrationUnlocked": clean_id_list(source.get("narrationUnlocked")),
        "relationUnlocked": clean_id_list(source.get("relationUnlocked")),
        "voiceReplayUnlocked": clean_id_list(source.get("voiceReplayUnlocked")),
        "endingUnlocked": clean_id_list(source.get("endingUnlocked")),
        "endingCompletionCount": max(0, int(source.get("endingCompletionCount") or 0)),
        "endingLastCompletedAt": str(source.get("endingLastCompletedAt") or "").strip() or None,
    }


def load_project_archive_progress(project_id: str) -> dict:
    progress_path = get_project_progress_file_path(project_id)
    if not progress_path.is_file():
        return sanitize_archive_progress(None)
    try:
        payload = json.loads(progress_path.read_text(encoding="utf-8"))
    except Exception:
        return sanitize_archive_progress(None)
    return sanitize_archive_progress(payload)


def write_project_archive_progress(project_id: str, progress: dict) -> Path:
    progress_dir = get_runtime_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)
    progress_path = get_project_progress_file_path(project_id)
    safe_payload = sanitize_archive_progress(progress)
    progress_path.write_text(json.dumps(safe_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return progress_path


def sanitize_runtime_player_settings(value: dict | None) -> dict:
    source = value or {}
    theme_mode = str(source.get("themeMode") or DEFAULT_RUNTIME_PLAYER_SETTINGS["themeMode"]).strip().lower()
    if theme_mode not in RUNTIME_THEME_MODES:
        theme_mode = DEFAULT_RUNTIME_PLAYER_SETTINGS["themeMode"]
    display_mode = str(source.get("displayMode") or DEFAULT_RUNTIME_PLAYER_SETTINGS["displayMode"]).strip().lower()
    if display_mode not in RUNTIME_DISPLAY_MODES:
        display_mode = DEFAULT_RUNTIME_PLAYER_SETTINGS["displayMode"]
    text_speed = str(source.get("textSpeed") or DEFAULT_RUNTIME_PLAYER_SETTINGS["textSpeed"]).strip().lower()
    if text_speed not in TEXT_SPEED_PRESETS:
        text_speed = DEFAULT_RUNTIME_PLAYER_SETTINGS["textSpeed"]
    return {
        "themeMode": theme_mode,
        "displayMode": display_mode,
        "textSpeed": text_speed,
        "masterVolume": clamp_int(source.get("masterVolume"), 0, 100, DEFAULT_RUNTIME_PLAYER_SETTINGS["masterVolume"]),
        "bgmVolume": clamp_int(source.get("bgmVolume"), 0, 100, DEFAULT_RUNTIME_PLAYER_SETTINGS["bgmVolume"]),
        "sfxVolume": clamp_int(source.get("sfxVolume"), 0, 100, DEFAULT_RUNTIME_PLAYER_SETTINGS["sfxVolume"]),
        "voiceVolume": clamp_int(source.get("voiceVolume"), 0, 100, DEFAULT_RUNTIME_PLAYER_SETTINGS["voiceVolume"]),
    }


def load_project_runtime_settings(project_id: str) -> dict:
    settings_path = get_project_settings_file_path(project_id)
    if not settings_path.is_file():
        return dict(DEFAULT_RUNTIME_PLAYER_SETTINGS)
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_RUNTIME_PLAYER_SETTINGS)
    return sanitize_runtime_player_settings(payload)


def write_project_runtime_settings(project_id: str, settings: dict) -> Path:
    settings_dir = get_runtime_settings_dir()
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_path = get_project_settings_file_path(project_id)
    safe_settings = sanitize_runtime_player_settings(settings)
    settings_path.write_text(json.dumps(safe_settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return settings_path


def format_snapshot_saved_at(saved_at: str | None) -> str:
    if not saved_at:
        return "尚未保存"
    try:
        parsed = datetime.fromisoformat(str(saved_at))
    except Exception:
        return str(saved_at)
    return parsed.strftime("%m-%d %H:%M")


def format_play_duration(milliseconds: int | float | None) -> str:
    try:
        total_seconds = max(0, int(float(milliseconds or 0) // 1000))
    except Exception:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours:
        return f"{hours} 小时 {minutes} 分钟"
    if minutes:
        return f"{minutes} 分钟 {seconds} 秒"
    return f"{seconds} 秒"


def build_save_dialog_page_data(
    project: dict | None,
    save_store: dict | None,
    page: int = 0,
    page_size: int = SAVE_DIALOG_PAGE_SIZE,
) -> dict:
    slot_count = get_project_formal_save_slot_count(project)
    safe_page_size = max(1, int(page_size or SAVE_DIALOG_PAGE_SIZE))
    page_count = max(1, (slot_count + safe_page_size - 1) // safe_page_size)
    current_page = max(0, min(page_count - 1, int(page or 0)))
    start = current_page * safe_page_size
    end = min(slot_count, start + safe_page_size)
    formal_slots = (save_store or {}).get("formalSlots") or [None] * slot_count
    formal_slots = list(formal_slots[:slot_count])
    while len(formal_slots) < slot_count:
        formal_slots.append(None)

    visible_slots = []
    for slot_index in range(start, end):
        snapshot = formal_slots[slot_index]
        scene_name = ""
        summary_text = "空位"
        saved_at = "尚未保存"
        if snapshot:
            scene_name = str(snapshot.get("sceneName") or snapshot.get("sceneId") or f"存档 {slot_index + 1}")
            summary_text = str(snapshot.get("summaryText") or "").strip() or "当前没有摘要。"
            saved_at = format_snapshot_saved_at(snapshot.get("savedAt"))
        visible_slots.append(
            {
                "slotIndex": slot_index,
                "label": f"正式存档 {slot_index + 1}",
                "isEmpty": snapshot is None,
                "sceneName": scene_name,
                "summaryText": summary_text,
                "savedAt": saved_at,
                "finished": bool(snapshot.get("finished")) if snapshot else False,
            }
        )

    quick_save = (save_store or {}).get("quickSave")
    quick_summary = {
        "isEmpty": quick_save is None,
        "sceneName": str((quick_save or {}).get("sceneName") or (quick_save or {}).get("sceneId") or ""),
        "summaryText": str((quick_save or {}).get("summaryText") or "").strip() or ("空" if quick_save is None else "当前没有摘要。"),
        "savedAt": format_snapshot_saved_at((quick_save or {}).get("savedAt")),
    }
    return {
        "slotCount": slot_count,
        "pageSize": safe_page_size,
        "pageCount": page_count,
        "page": current_page,
        "startIndex": start,
        "endIndex": end,
        "quickSave": quick_summary,
        "visibleSlots": visible_slots,
    }


def write_project_save_store(project_id: str, save_store: dict) -> Path:
    save_dir = get_runtime_save_dir()
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = get_project_save_file_path(project_id)
    save_path.write_text(json.dumps(save_store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return save_path


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def get_block_label(block_type: str) -> str:
    return {
        "dialogue": "台词",
        "narration": "旁白",
        "choice": "选项",
        "jump": "跳转",
        "condition": "条件判断",
        "background": "背景",
        "character_show": "显示角色",
        "character_hide": "隐藏角色",
        "music_play": "播放音乐",
        "music_stop": "停止音乐",
        "sfx_play": "播放音效",
        "video_play": "播放视频",
        "credits_roll": "片尾字幕",
        "particle_effect": "粒子特效",
        "screen_shake": "屏幕震动",
        "screen_flash": "闪屏",
        "screen_fade": "黑场淡入淡出",
        "camera_zoom": "镜头推近拉远",
        "camera_pan": "镜头平移",
        "screen_filter": "画面滤镜",
        "depth_blur": "景深模糊",
    }.get(block_type, block_type or "未知")


def get_asset_runtime_path(bundle_dir: Path, asset: dict | None) -> Path | None:
    if not asset or asset.get("isMissing"):
        return None
    export_url = str(asset.get("exportUrl") or "").strip()
    if not export_url:
        return None
    candidate = bundle_dir / export_url
    return candidate if candidate.is_file() else None


def wrap_text(font, text: str, max_width: int) -> list[str]:
    if not text:
        return [""]

    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [text]


class NativeRuntimePlayer:
    def __init__(self, pygame, game_data_path: Path) -> None:
        self.pygame = pygame
        self.bundle_dir = game_data_path.parent
        self.data = load_game_data(game_data_path)
        self.project = self.data.get("project") or {}
        self.assets = (self.data.get("assets") or {}).get("assets") or []
        self.characters = (self.data.get("characters") or {}).get("characters") or []
        self.variables = (self.data.get("variables") or {}).get("variables") or []
        self.chapters = self.data.get("chapters") or []
        self.build_info = self.data.get("buildInfo") or {}
        self.dialog_box_config = get_project_dialog_box_config(self.project)
        self.game_ui_config = get_project_game_ui_config(self.project)

        self.assets_by_id = {asset.get("id"): asset for asset in self.assets if asset.get("id")}
        self.characters_by_id = {character.get("id"): character for character in self.characters if character.get("id")}
        self.scenes_by_id = {}
        self.scene_order = []
        for chapter in self.chapters:
            for scene in chapter.get("scenes", []) or []:
                scene_id = scene.get("id")
                if scene_id:
                    self.scenes_by_id[scene_id] = scene
                    self.scene_order.append(scene_id)

        if not self.scenes_by_id:
            raise NativeRuntimeError("游戏数据里没有任何场景。")

        resolution = self.project.get("resolution") or {}
        self.width = int(resolution.get("width") or 1280)
        self.height = int(resolution.get("height") or 720)
        self.formal_save_slot_count = get_project_formal_save_slot_count(self.project)
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.active_display_mode = "windowed"
        pygame.display.set_caption(f"{self.project.get('title') or 'Tony Na Engine'} · 原生 Runtime")

        self.font_small = self._create_font(22)
        self.font_body = self._create_font(30)
        self.font_title = self._create_font(36, bold=True)
        self.font_ui = self._create_font(18)
        self.image_cache: dict[str, object] = {}
        self.image_file_cache: dict[str, object] = {}
        self.sound_cache: dict[str, object] = {}
        self.current_bgm_asset_id: str | None = None
        self.current_voice_channel = None
        self.project_id = str(self.project.get("projectId") or "untitled_project")
        self.save_store = load_project_save_store(self.project_id, self.formal_save_slot_count)
        self.save_file_path = get_project_save_file_path(self.project_id)
        self.runtime_settings = load_project_runtime_settings(self.project_id)
        self.settings_file_path = get_project_settings_file_path(self.project_id)
        self.archive_progress = load_project_archive_progress(self.project_id)
        self.progress_file_path = get_project_progress_file_path(self.project_id)
        self.player_profile = load_project_player_profile(self.project_id)
        self.profile_file_path = get_project_profile_file_path(self.project_id)
        self.auto_resume_snapshot = load_project_auto_resume(self.project_id)
        self.auto_resume_file_path = get_project_auto_resume_file_path(self.project_id)
        self.auto_resume_write_enabled = self.auto_resume_snapshot is None
        self.profile_session_started_at_ms = 0
        self.overlay_mode: str | None = None
        self.overlay_page = 0
        self.overlay_focus_index = 0
        self.overlay_hotspots: list[dict] = []
        self.video_hotspots: list[dict] = []
        self.video_preview_frame_cache: dict[str, dict] = {}
        self.system_menu_index = 0
        self.title_menu_index = 0
        self.settings_menu_index = 0
        self.archive_selection_index = 0
        self.current_archive_key = "chapters"
        self.archive_detail_key: str | None = None
        self.archive_detail_entry: dict | None = None
        self.current_line_started_at_ms = 0
        self.current_line_full_text = ""
        self.current_line_revealed_chars = 0
        self.runtime_elapsed_seconds = 0.0
        self.active_particle_effect: dict | None = None
        self.particle_items: list[dict] = []
        self.screen_shake_effect: dict | None = None
        self.screen_flash_effect: dict | None = None
        self.screen_fade_effect: dict | None = None
        self.camera_zoom_effect: dict | None = None
        self.camera_pan_effect: dict | None = None
        self.screen_filter_effect: dict | None = None
        self.depth_blur_effect: dict | None = None

        self.variable_state = {
            variable.get("id"): variable.get("defaultValue")
            for variable in self.variables
            if variable.get("id")
        }
        self.stage_background_asset_id: str | None = None
        self.visible_characters: dict[str, dict] = {}
        self.current_scene_id = self.project.get("entrySceneId") or self.scene_order[0]
        if self.current_scene_id not in self.scenes_by_id:
            self.current_scene_id = self.scene_order[0]
        self.unlock_current_chapter_replay()
        self.current_block_index = 0
        self.current_line: dict | None = None
        self.current_choices: list[dict] | None = None
        self.current_choice_index = 0
        self.title_screen_active = False
        self.finished = False
        self.finished_message = ""
        self.status_message = "正在初始化原生 Runtime…"

        self._initialize_audio()
        self.apply_runtime_settings()
        self.record_player_session_start()
        self.open_title_screen()

    def _create_font(self, size: int, bold: bool = False):
        candidates = [
            "PingFang SC",
            "Hiragino Sans GB",
            "Microsoft YaHei",
            "Noto Sans CJK SC",
            "Source Han Sans SC",
            "WenQuanYi Zen Hei",
            "SimHei",
            "Arial Unicode MS",
        ]
        for name in candidates:
            try:
                font = self.pygame.font.SysFont(name, size, bold=bold)
                if font:
                    return font
            except Exception:
                continue
        return self.pygame.font.Font(None, size)

    def _initialize_audio(self) -> None:
        try:
            self.pygame.mixer.init()
        except Exception:
            self.status_message = "当前设备没有初始化音频输出，运行时会继续，但音乐和语音不会播放。"

    def get_effective_volume(self, channel_key: str) -> float:
        master = clamp(float(self.runtime_settings.get("masterVolume", 100)) / 100, 0.0, 1.0)
        channel = clamp(float(self.runtime_settings.get(channel_key, 100)) / 100, 0.0, 1.0)
        return master * channel

    def apply_runtime_settings(self) -> None:
        self.apply_display_mode()
        if self.pygame.mixer.get_init():
            try:
                self.pygame.mixer.music.set_volume(self.get_effective_volume("bgmVolume"))
            except Exception:
                pass
        if self.current_voice_channel:
            try:
                self.current_voice_channel.set_volume(self.get_effective_volume("voiceVolume"))
            except Exception:
                pass

    def apply_display_mode(self) -> None:
        display_mode = str(self.runtime_settings.get("displayMode") or "windowed")
        if display_mode == getattr(self, "active_display_mode", "windowed"):
            return
        flags = self.pygame.FULLSCREEN if display_mode == "fullscreen" else 0
        try:
            self.screen = self.pygame.display.set_mode((self.width, self.height), flags)
            self.active_display_mode = display_mode
        except Exception:
            if display_mode == "fullscreen":
                self.runtime_settings["displayMode"] = "windowed"
                self.screen = self.pygame.display.set_mode((self.width, self.height))
                self.active_display_mode = "windowed"
                self.status_message = "全屏切换失败，已回到窗口模式。"

    def toggle_display_mode(self) -> None:
        current = str(self.runtime_settings.get("displayMode") or "windowed")
        self.runtime_settings["displayMode"] = "fullscreen" if current == "windowed" else "windowed"
        self.runtime_settings = sanitize_runtime_player_settings(self.runtime_settings)
        self.apply_display_mode()
        self.persist_runtime_settings()
        label = "全屏" if self.runtime_settings.get("displayMode") == "fullscreen" else "窗口"
        self.status_message = f"显示模式已切换为：{label}"

    def persist_runtime_settings(self) -> None:
        write_project_runtime_settings(self.project_id, self.runtime_settings)

    def persist_archive_progress(self) -> None:
        write_project_archive_progress(self.project_id, self.archive_progress)

    def persist_player_profile(self) -> None:
        self.player_profile = sanitize_player_profile(self.player_profile)
        write_project_player_profile(self.project_id, self.player_profile)

    def record_player_session_start(self) -> None:
        now = now_iso()
        profile = sanitize_player_profile(self.player_profile)
        if not profile.get("firstPlayedAt"):
            profile["firstPlayedAt"] = now
        profile["lastPlayedAt"] = now
        profile["sessionCount"] = int(profile.get("sessionCount") or 0) + 1
        self.player_profile = profile
        self.profile_session_started_at_ms = self.pygame.time.get_ticks()
        self.persist_player_profile()

    def record_player_session_end(self) -> None:
        profile = sanitize_player_profile(self.player_profile)
        if self.profile_session_started_at_ms:
            elapsed_ms = max(0, self.pygame.time.get_ticks() - self.profile_session_started_at_ms)
            profile["totalPlayMs"] = int(profile.get("totalPlayMs") or 0) + elapsed_ms
            self.profile_session_started_at_ms = 0
        profile["lastEndedAt"] = now_iso()
        self.player_profile = profile
        self.persist_player_profile()

    def record_player_resume(self) -> None:
        profile = sanitize_player_profile(self.player_profile)
        profile["resumedCount"] = int(profile.get("resumedCount") or 0) + 1
        profile["lastPlayedAt"] = now_iso()
        self.player_profile = profile
        self.persist_player_profile()

    def record_player_return_to_start(self) -> None:
        profile = sanitize_player_profile(self.player_profile)
        profile["returnToTitleCount"] = int(profile.get("returnToTitleCount") or 0) + 1
        profile["lastPlayedAt"] = now_iso()
        self.player_profile = profile
        self.persist_player_profile()

    def persist_auto_resume_snapshot(self) -> None:
        if not self.auto_resume_write_enabled:
            return
        snapshot = self.build_save_snapshot("auto-resume")
        self.auto_resume_snapshot = sanitize_auto_resume_snapshot(snapshot)
        if self.auto_resume_snapshot:
            write_project_auto_resume(self.project_id, self.auto_resume_snapshot)

    def clear_auto_resume_snapshot(self) -> None:
        clear_project_auto_resume(self.project_id)
        self.auto_resume_snapshot = None
        self.auto_resume_write_enabled = False
        self.status_message = "续玩记录已清除。"

    def load_auto_resume_snapshot(self) -> None:
        snapshot = self.auto_resume_snapshot or load_project_auto_resume(self.project_id)
        if not snapshot:
            self.status_message = "当前还没有续玩记录。"
            return
        self.restore_from_snapshot(snapshot)
        self.record_player_resume()
        self.persist_auto_resume_snapshot()
        self.close_overlay(preserve_status=True)
        self.status_message = f"已续玩：{snapshot.get('sceneName') or '未命名场景'}"

    def get_active_theme_mode(self) -> str:
        selected = str(self.runtime_settings.get("themeMode") or "auto")
        if selected == "auto":
            hour = datetime.now().hour
            return "light" if 7 <= hour < 19 else "dark"
        return selected

    def get_active_palette(self) -> dict:
        if self.get_active_theme_mode() == "light":
            palette = {
                "bgTop": (223, 232, 244),
                "bgBottom": (246, 249, 255),
                "panel": (245, 249, 255),
                "panelAlpha": 236,
                "panelBorder": (120, 156, 214),
                "text": (34, 47, 73),
                "muted": (92, 108, 132),
                "accent": (72, 122, 228),
                "accentAlt": (140, 90, 236),
                "warning": (220, 128, 86),
                "overlay": (220, 228, 242, 172),
                "placeholder": (220, 230, 244),
            }
        else:
            palette = {
                "bgTop": (18, 32, 58),
                "bgBottom": (24, 18, 48),
                "panel": COLOR_PANEL,
                "panelAlpha": 230,
                "panelBorder": COLOR_PANEL_BORDER,
                "text": COLOR_TEXT,
                "muted": COLOR_TEXT_MUTED,
                "accent": COLOR_ACCENT,
                "accentAlt": COLOR_ACCENT_ALT,
                "warning": COLOR_WARNING,
                "overlay": (6, 10, 18, 188),
                "placeholder": (36, 46, 77),
            }

        game_ui = getattr(self, "game_ui_config", None) or {}
        if game_ui:
            bg = game_ui.get("backgroundColor", palette["bgBottom"])
            accent = game_ui.get("backgroundAccentColor", palette["accent"])
            panel = game_ui.get("panelColor", palette["panel"])
            border = game_ui.get("borderColor", palette["panelBorder"])
            palette.update(
                {
                    "bgTop": mix_rgb(bg, accent, 0.18),
                    "bgBottom": mix_rgb(bg, (0, 0, 0), 0.18),
                    "panel": panel,
                    "panelAlpha": int(round(clamp_int(game_ui.get("panelOpacity"), 35, 100, 88) * 2.55)),
                    "panelBorder": border,
                    "text": game_ui.get("textColor", palette["text"]),
                    "muted": game_ui.get("mutedTextColor", palette["muted"]),
                    "accent": game_ui.get("accentColor", palette["accent"]),
                    "accentAlt": game_ui.get("accentAltColor", palette["accentAlt"]),
                    "overlay": (*mix_rgb(bg, (0, 0, 0), 0.22), 188),
                    "placeholder": mix_rgb(panel, accent, 0.12),
                }
            )
        return palette

    def unlock_archive_entry(self, progress_key: str, entry_id: str | None) -> None:
        safe_id = str(entry_id or "").strip()
        if not safe_id:
            return
        entries = self.archive_progress.setdefault(progress_key, [])
        if safe_id in entries:
            return
        entries.append(safe_id)
        self.archive_progress = sanitize_archive_progress(self.archive_progress)
        self.persist_archive_progress()

    def build_scene_preview(self, scene: dict | None) -> dict:
        preview = {
            "backgroundAssetId": "",
            "speakerName": "",
            "dialogueText": "",
        }
        if not scene:
            return preview
        for block in scene.get("blocks", []) or []:
            block_type = str(block.get("type") or "").strip()
            if block_type == "background" and block.get("assetId"):
                preview["backgroundAssetId"] = str(block.get("assetId") or "")
            elif block_type in {"dialogue", "narration"}:
                preview["dialogueText"] = str(block.get("text") or "").strip()
                speaker_id = str(block.get("speakerId") or "").strip()
                if speaker_id:
                    speaker = self.characters_by_id.get(speaker_id) or {}
                    preview["speakerName"] = str(speaker.get("displayName") or speaker_id)
                elif block_type == "narration":
                    preview["speakerName"] = "旁白"
        return preview

    def collect_scene_encounter_character_ids(self, scene: dict | None, max_block_index: int | None = None) -> list[str]:
        if not scene:
            return []
        seen_ids: set[str] = set()
        ordered_ids: list[str] = []
        limit = max_block_index if max_block_index is not None else 10**9
        for block_index, block in enumerate(scene.get("blocks", []) or []):
            if block_index > limit:
                break
            candidates = []
            speaker_id = str(block.get("speakerId") or "").strip()
            character_id = str(block.get("characterId") or "").strip()
            if speaker_id:
                candidates.append(speaker_id)
            if character_id:
                candidates.append(character_id)
            for candidate in candidates:
                if candidate not in self.characters_by_id or candidate in seen_ids:
                    continue
                seen_ids.add(candidate)
                ordered_ids.append(candidate)
        return ordered_ids

    def get_chapter_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("chapterReplayUnlocked") or [])
        entries = []
        for order, chapter in enumerate(self.chapters, start=1):
            scenes = chapter.get("scenes") or []
            first_scene = scenes[0] if scenes else {}
            preview = self.build_scene_preview(first_scene)
            chapter_id = str(chapter.get("chapterId") or "")
            entries.append(
                {
                    "id": chapter_id,
                    "name": str(chapter.get("name") or f"第 {order} 章"),
                    "subtitle": f"{len(scenes)} 个场景 · 开头：{first_scene.get('name') or '未命名场景'}",
                    "notes": str(chapter.get("summary") or chapter.get("notes") or ""),
                    "actionLabel": "重放这一章",
                    "actionEnabled": chapter_id in unlocked_ids and bool(first_scene.get("id")),
                    "firstSceneId": str(first_scene.get("id") or ""),
                    "previewAssetId": preview["backgroundAssetId"],
                    "previewSpeakerName": preview["speakerName"],
                    "previewText": preview["dialogueText"],
                    "unlocked": chapter_id in unlocked_ids,
                }
            )
        return entries

    def get_music_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("bgmUnlocked") or [])
        entries = []
        for asset in self.assets:
            if asset.get("type") != "bgm" or not asset.get("id"):
                continue
            tags = " / ".join(asset.get("tags") or [])
            entries.append(
                {
                    "id": str(asset["id"]),
                    "name": str(asset.get("name") or asset["id"]),
                    "subtitle": tags or "BGM 曲目",
                    "notes": str(asset.get("notes") or ""),
                    "actionLabel": "播放这首",
                    "actionEnabled": str(asset["id"]) in unlocked_ids,
                    "unlocked": str(asset["id"]) in unlocked_ids,
                    "previewSpeakerName": "音乐鉴赏",
                    "previewText": str(asset.get("notes") or "解锁后可以直接播放这首 BGM。"),
                }
            )
        return entries

    def get_gallery_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("cgUnlocked") or [])
        entries = []
        for asset in self.assets:
            if asset.get("type") != "cg" or not asset.get("id"):
                continue
            tags = " / ".join(asset.get("tags") or [])
            entries.append(
                {
                    "id": str(asset["id"]),
                    "name": str(asset.get("name") or asset["id"]),
                    "subtitle": tags or "CG 条目",
                    "notes": str(asset.get("notes") or ""),
                    "actionLabel": "查看大图",
                    "actionEnabled": str(asset["id"]) in unlocked_ids,
                    "previewAssetId": str(asset["id"]),
                    "previewText": str(asset.get("notes") or "推进到对应演出后，这张 CG 会在这里亮起。"),
                    "unlocked": str(asset["id"]) in unlocked_ids,
                }
            )
        return entries

    def get_location_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("locationUnlocked") or [])
        seen_asset_ids: set[str] = set()
        entries = []
        for chapter in self.chapters:
            chapter_name = str(chapter.get("name") or "未命名章节")
            for scene in chapter.get("scenes") or []:
                for block in scene.get("blocks", []) or []:
                    if str(block.get("type") or "").strip() != "background":
                        continue
                    asset_id = str(block.get("assetId") or "").strip()
                    if not asset_id or asset_id in seen_asset_ids:
                        continue
                    asset = self.assets_by_id.get(asset_id) or {}
                    if asset.get("type") != "background":
                        continue
                    seen_asset_ids.add(asset_id)
                    tags = " / ".join(asset.get("tags") or [])
                    entries.append(
                        {
                            "id": asset_id,
                            "name": str(asset.get("name") or asset_id),
                            "subtitle": f"{chapter_name} · {scene.get('name') or '未命名场景'}",
                            "notes": tags or "推进到这张背景第一次出现的位置后会自动收录。",
                            "actionLabel": "查看地点",
                            "actionEnabled": asset_id in unlocked_ids,
                            "previewAssetId": asset_id,
                            "previewText": str(tags or "这个地点来自剧情里的背景切换。"),
                            "unlocked": asset_id in unlocked_ids,
                        }
                    )
        return entries

    def get_character_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("characterUnlocked") or [])
        entries = []
        for character in self.characters:
            character_id = str(character.get("id") or "").strip()
            if not character_id:
                continue
            expressions = character.get("expressions") or []
            entries.append(
                {
                    "id": character_id,
                    "name": str(character.get("displayName") or character_id),
                    "subtitle": f"{character.get('defaultPosition') or 'center'} · {len(expressions)} 个表情",
                    "notes": str(character.get("bio") or "推进到角色出场或开口后自动收录。"),
                    "actionLabel": "查看角色",
                    "actionEnabled": character_id in unlocked_ids,
                    "previewAssetId": str(character.get("defaultSpriteId") or ""),
                    "previewText": str(character.get("bio") or "这个角色会在剧情推进后自动收录进图鉴。"),
                    "unlocked": character_id in unlocked_ids,
                }
            )
        return entries

    def get_narration_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("narrationUnlocked") or [])
        entries = []
        for chapter in self.chapters:
            chapter_name = str(chapter.get("name") or "未命名章节")
            for scene in chapter.get("scenes") or []:
                current_background_asset_id = ""
                for block_index, block in enumerate(scene.get("blocks", []) or []):
                    block_type = str(block.get("type") or "").strip()
                    if block_type == "background" and block.get("assetId"):
                        current_background_asset_id = str(block.get("assetId") or "")
                    if block_type != "narration":
                        continue
                    text = str(block.get("text") or "").strip()
                    if not text:
                        continue
                    entry_id = build_narration_archive_entry_id(scene.get("id"), block.get("id"), block_index)
                    entries.append(
                        {
                            "id": entry_id,
                            "name": f"{chapter_name} · {scene.get('name') or '未命名场景'}",
                            "subtitle": f"第 {block_index + 1} 条摘录",
                            "notes": text[:80],
                            "actionLabel": "查看摘录",
                            "actionEnabled": entry_id in unlocked_ids,
                            "previewAssetId": current_background_asset_id,
                            "previewSpeakerName": "旁白",
                            "previewText": text,
                            "unlocked": entry_id in unlocked_ids,
                        }
                    )
        return entries

    def get_relation_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("relationUnlocked") or [])
        entries = []
        seen_pair_ids: set[str] = set()
        for chapter in self.chapters:
            chapter_name = str(chapter.get("name") or "未命名章节")
            for scene in chapter.get("scenes") or []:
                scene_character_ids = self.collect_scene_encounter_character_ids(scene)
                if len(scene_character_ids) < 2:
                    continue
                preview = self.build_scene_preview(scene)
                for index, left_character_id in enumerate(scene_character_ids):
                    for right_character_id in scene_character_ids[index + 1 :]:
                        pair_id = build_relationship_archive_id(left_character_id, right_character_id)
                        if not pair_id or pair_id in seen_pair_ids:
                            continue
                        seen_pair_ids.add(pair_id)
                        left_character = self.characters_by_id.get(left_character_id) or {}
                        right_character = self.characters_by_id.get(right_character_id) or {}
                        entries.append(
                            {
                                "id": pair_id,
                                "name": f"{left_character.get('displayName') or left_character_id} × {right_character.get('displayName') or right_character_id}",
                                "subtitle": f"{chapter_name} · {scene.get('name') or '未命名场景'}",
                                "notes": preview["dialogueText"] or "推进到这组角色真正同场后会自动收录。",
                                "actionLabel": "查看关系",
                                "actionEnabled": pair_id in unlocked_ids,
                                "previewAssetId": preview["backgroundAssetId"],
                                "previewSpeakerName": preview["speakerName"],
                                "previewText": preview["dialogueText"],
                                "unlocked": pair_id in unlocked_ids,
                            }
                        )
        return entries

    def get_voice_replay_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("voiceReplayUnlocked") or [])
        entries = []
        for chapter in self.chapters:
            chapter_name = str(chapter.get("name") or "未命名章节")
            for scene in chapter.get("scenes") or []:
                current_background_asset_id = ""
                for block_index, block in enumerate(scene.get("blocks", []) or []):
                    block_type = str(block.get("type") or "").strip()
                    if block_type == "background" and block.get("assetId"):
                        current_background_asset_id = str(block.get("assetId") or "")
                    if block_type not in {"dialogue", "narration"} or not block.get("voiceAssetId"):
                        continue
                    text = str(block.get("text") or "").strip()
                    entry_id = build_voice_replay_entry_id(scene.get("id"), block.get("id"), block_index)
                    speaker_id = str(block.get("speakerId") or "").strip()
                    speaker_name = ""
                    if speaker_id:
                        speaker_name = str((self.characters_by_id.get(speaker_id) or {}).get("displayName") or speaker_id)
                    elif block_type == "narration":
                        speaker_name = "旁白"
                    entries.append(
                        {
                            "id": entry_id,
                            "name": speaker_name or f"{chapter_name} · {scene.get('name') or '未命名场景'}",
                            "subtitle": f"{chapter_name} · {scene.get('name') or '未命名场景'}",
                            "notes": text[:80] or "这句带语音的台词会在推进后自动收录。",
                            "actionLabel": "回放语音",
                            "actionEnabled": entry_id in unlocked_ids,
                            "voiceAssetId": str(block.get("voiceAssetId") or ""),
                            "previewAssetId": current_background_asset_id,
                            "previewSpeakerName": speaker_name,
                            "previewText": text,
                            "unlocked": entry_id in unlocked_ids,
                        }
                    )
        return entries

    def get_ending_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("endingUnlocked") or [])
        entries = []
        for chapter in self.chapters:
            chapter_name = str(chapter.get("name") or "未命名章节")
            for scene in chapter.get("scenes") or []:
                scene_id = str(scene.get("id") or "").strip()
                if not scene_id or collect_scene_outgoing_targets(scene):
                    continue
                preview = self.build_scene_preview(scene)
                entries.append(
                    {
                        "id": scene_id,
                        "name": str(scene.get("name") or scene_id),
                        "subtitle": chapter_name,
                        "notes": str(scene.get("notes") or "推进到这条路线收束位置后会自动回收到这里。"),
                        "actionLabel": "回放结局",
                        "actionEnabled": scene_id in unlocked_ids,
                        "previewAssetId": preview["backgroundAssetId"],
                        "previewSpeakerName": preview["speakerName"],
                        "previewText": preview["dialogueText"],
                        "unlocked": scene_id in unlocked_ids,
                    }
                )
        return entries

    def get_achievement_archive_entries(self) -> list[dict]:
        character_entries = self.get_character_archive_entries()
        gallery_entries = self.get_gallery_archive_entries()
        music_entries = self.get_music_archive_entries()
        ending_entries = self.get_ending_archive_entries()

        unlocked_characters = sum(1 for entry in character_entries if entry.get("unlocked"))
        unlocked_cg = sum(1 for entry in gallery_entries if entry.get("unlocked"))
        unlocked_bgm = sum(1 for entry in music_entries if entry.get("unlocked"))
        unlocked_endings = sum(1 for entry in ending_entries if entry.get("unlocked"))

        definitions = [
            {
                "id": "first_start",
                "name": "初次启动",
                "subtitle": "第一次进入原生 Runtime",
                "notes": "启动一次原生 Runtime 即可点亮。",
                "unlocked": bool(self.scene_order),
            },
            {
                "id": "first_character",
                "name": "角色初见",
                "subtitle": f"已收录角色 {unlocked_characters} / {len(character_entries)}",
                "notes": "任意角色完成收录后点亮。",
                "unlocked": unlocked_characters > 0,
            },
            {
                "id": "all_characters",
                "name": "角色全收录",
                "subtitle": f"已收录角色 {unlocked_characters} / {len(character_entries)}",
                "notes": "收录全部角色图鉴后点亮。",
                "unlocked": bool(character_entries) and unlocked_characters >= len(character_entries),
            },
            {
                "id": "first_cg",
                "name": "CG 初见",
                "subtitle": f"已回收 CG {unlocked_cg} / {len(gallery_entries)}",
                "notes": "任意 CG 完成回收后点亮。",
                "unlocked": unlocked_cg > 0,
            },
            {
                "id": "all_cg",
                "name": "CG 全回收",
                "subtitle": f"已回收 CG {unlocked_cg} / {len(gallery_entries)}",
                "notes": "回收全部 CG 后点亮。",
                "unlocked": bool(gallery_entries) and unlocked_cg >= len(gallery_entries),
            },
            {
                "id": "first_bgm",
                "name": "乐曲初见",
                "subtitle": f"已解锁曲目 {unlocked_bgm} / {len(music_entries)}",
                "notes": "任意 BGM 完成解锁后点亮。",
                "unlocked": unlocked_bgm > 0,
            },
            {
                "id": "all_bgm",
                "name": "乐曲全解锁",
                "subtitle": f"已解锁曲目 {unlocked_bgm} / {len(music_entries)}",
                "notes": "解锁全部 BGM 后点亮。",
                "unlocked": bool(music_entries) and unlocked_bgm >= len(music_entries),
            },
            {
                "id": "first_ending",
                "name": "初次通关",
                "subtitle": f"已回收结局 {unlocked_endings} / {len(ending_entries)}",
                "notes": "任意结局完成回收后点亮。",
                "unlocked": unlocked_endings > 0,
            },
            {
                "id": "all_endings",
                "name": "结局全回收",
                "subtitle": f"已回收结局 {unlocked_endings} / {len(ending_entries)}",
                "notes": "回收全部结局后点亮。",
                "unlocked": bool(ending_entries) and unlocked_endings >= len(ending_entries),
            },
        ]

        return [
            {
                **entry,
                "actionLabel": "查看成就",
                "actionEnabled": bool(entry.get("unlocked")),
                "previewText": entry["notes"],
            }
            for entry in definitions
        ]

    def get_archive_entries(self, archive_key: str) -> list[dict]:
        if archive_key == "achievements":
            return self.get_achievement_archive_entries()
        if archive_key == "narrations":
            return self.get_narration_archive_entries()
        if archive_key == "relations":
            return self.get_relation_archive_entries()
        if archive_key == "voices":
            return self.get_voice_replay_entries()
        if archive_key == "locations":
            return self.get_location_archive_entries()
        if archive_key == "characters":
            return self.get_character_archive_entries()
        if archive_key == "endings":
            return self.get_ending_archive_entries()
        if archive_key == "music":
            return self.get_music_archive_entries()
        if archive_key == "gallery":
            return self.get_gallery_archive_entries()
        return self.get_chapter_archive_entries()

    def get_selected_archive_entry(self) -> dict | None:
        entries = self.get_archive_entries(self.current_archive_key)
        if not entries:
            return None
        self.archive_selection_index = max(0, min(len(entries) - 1, self.archive_selection_index))
        return entries[self.archive_selection_index]

    def get_visible_archive_window(self, entries: list[dict], limit: int = 9) -> tuple[int, list[tuple[int, dict]]]:
        if not entries:
            return 0, []
        safe_limit = max(1, int(limit or 9))
        if len(entries) <= safe_limit:
            return 0, list(enumerate(entries))
        current_index = max(0, min(len(entries) - 1, self.archive_selection_index))
        max_start = max(0, len(entries) - safe_limit)
        start = max(0, min(max_start, current_index - safe_limit // 2))
        end = min(len(entries), start + safe_limit)
        start = max(0, end - safe_limit)
        return start, list(enumerate(entries[start:end], start=start))

    def change_archive_tab(self, delta: int) -> None:
        if not ARCHIVE_MENU_SEQUENCE:
            return
        try:
            current_index = ARCHIVE_MENU_SEQUENCE.index(self.current_archive_key)
        except ValueError:
            current_index = 0
        self.current_archive_key = ARCHIVE_MENU_SEQUENCE[(current_index + delta) % len(ARCHIVE_MENU_SEQUENCE)]
        self.archive_selection_index = 0

    def is_ending_scene(self, scene_id: str | None) -> bool:
        safe_scene_id = str(scene_id or "").strip()
        if not safe_scene_id:
            return False
        scene = self.scenes_by_id.get(safe_scene_id)
        return bool(scene) and not collect_scene_outgoing_targets(scene)

    def record_ending_completion(self, scene_id: str | None) -> None:
        safe_scene_id = str(scene_id or "").strip()
        if not self.is_ending_scene(safe_scene_id):
            return
        before_unlocked = set(self.archive_progress.get("endingUnlocked") or [])
        self.unlock_archive_entry("endingUnlocked", safe_scene_id)
        self.archive_progress["endingCompletionCount"] = max(
            0,
            int(self.archive_progress.get("endingCompletionCount") or 0),
        ) + 1
        self.archive_progress["endingLastCompletedAt"] = now_iso()
        self.archive_progress = sanitize_archive_progress(self.archive_progress)
        self.persist_archive_progress()
        if safe_scene_id not in before_unlocked:
            self.status_message = "结局已回收。"

    def start_current_line_display(self, text: str) -> None:
        self.current_line_full_text = str(text or "")
        self.current_line_revealed_chars = 0
        self.current_line_started_at_ms = self.pygame.time.get_ticks()
        if self.runtime_settings.get("textSpeed") == "instant":
            self.reveal_current_line_immediately()

    def reveal_current_line_immediately(self) -> None:
        self.current_line_revealed_chars = len(self.current_line_full_text)

    def is_current_line_fully_visible(self) -> bool:
        return self.current_line_revealed_chars >= len(self.current_line_full_text)

    def update_current_line_reveal(self) -> None:
        if not self.current_line or self.is_current_line_fully_visible():
            return
        chars_per_second = TEXT_SPEED_PRESETS.get(
            str(self.runtime_settings.get("textSpeed") or "normal"),
            TEXT_SPEED_PRESETS["normal"],
        )
        elapsed_ms = max(0, self.pygame.time.get_ticks() - self.current_line_started_at_ms)
        revealed = min(len(self.current_line_full_text), int(elapsed_ms / 1000 * chars_per_second))
        self.current_line_revealed_chars = max(self.current_line_revealed_chars, revealed)

    def get_current_line_render_text(self) -> str:
        self.update_current_line_reveal()
        return self.current_line_full_text[: self.current_line_revealed_chars]

    def handle_scene_finished(self, scene: dict | None) -> None:
        self.unlock_relation_entries_for_scene(scene)
        scene_id = str((scene or {}).get("id") or "").strip()
        if self.is_ending_scene(scene_id):
            self.record_ending_completion(scene_id)
        self.finished = True
        self.finished_message = "剧情已经结束。"

    def unlock_relation_entries_for_scene(self, scene: dict | None, max_block_index: int | None = None) -> None:
        scene_character_ids = self.collect_scene_encounter_character_ids(scene, max_block_index=max_block_index)
        if len(scene_character_ids) < 2:
            return
        for index, left_character_id in enumerate(scene_character_ids):
            for right_character_id in scene_character_ids[index + 1 :]:
                pair_id = build_relationship_archive_id(left_character_id, right_character_id)
                if pair_id:
                    self.unlock_archive_entry("relationUnlocked", pair_id)

    def sync_archive_progress_for_pause(self, scene: dict | None, block: dict, block_index: int) -> None:
        block_type = str(block.get("type") or "").strip()
        if block_type == "narration":
            narration_id = build_narration_archive_entry_id((scene or {}).get("id"), block.get("id"), block_index)
            self.unlock_archive_entry("narrationUnlocked", narration_id)
        if block_type in {"dialogue", "narration"} and block.get("voiceAssetId"):
            voice_id = build_voice_replay_entry_id((scene or {}).get("id"), block.get("id"), block_index)
            self.unlock_archive_entry("voiceReplayUnlocked", voice_id)
        self.unlock_relation_entries_for_scene(scene, max_block_index=block_index)

    def _load_image(self, asset_id: str | None):
        if not asset_id:
            return None
        if asset_id in self.image_cache:
            return self.image_cache[asset_id]
        asset = self.assets_by_id.get(asset_id)
        asset_path = get_asset_runtime_path(self.bundle_dir, asset)
        if not asset_path:
            self.image_cache[asset_id] = None
            return None
        try:
            image = self.pygame.image.load(str(asset_path)).convert_alpha()
        except Exception:
            image = None
        self.image_cache[asset_id] = image
        return image

    def _load_image_file(self, image_path: Path | None):
        if not image_path:
            return None
        cache_key = str(image_path)
        if cache_key in self.image_file_cache:
            return self.image_file_cache[cache_key]
        if not image_path.is_file():
            self.image_file_cache[cache_key] = None
            return None
        try:
            image = self.pygame.image.load(str(image_path)).convert_alpha()
        except Exception:
            image = None
        self.image_file_cache[cache_key] = image
        return image

    def get_engine_brand_logo_path(self) -> Path | None:
        candidates = [
            self.bundle_dir / ENGINE_BRAND_LOGO_RELATIVE_PATH,
            Path(__file__).resolve().parent / ENGINE_BRAND_LOGO_RELATIVE_PATH,
            Path(__file__).resolve().parent.parent / "prototype_editor" / "assets" / "brand-logo.png",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def get_title_logo_image(self):
        title_logo_asset_id = str(self.game_ui_config.get("titleLogoAssetId") or "").strip()
        if title_logo_asset_id:
            title_logo = self._load_image(title_logo_asset_id)
            if title_logo:
                return title_logo
        return self._load_image_file(self.get_engine_brand_logo_path())

    def draw_nine_slice_image(self, source, rect, slice_config: dict | None, opacity_percent: int) -> None:
        if not source or rect.width <= 0 or rect.height <= 0:
            return
        opacity = clamp_int(opacity_percent, 0, 100, 0)
        if opacity <= 0:
            return

        pygame = self.pygame
        source_width, source_height = source.get_size()
        if source_width <= 0 or source_height <= 0:
            return

        slice_source = slice_config if isinstance(slice_config, dict) else {}
        left = clamp_int(slice_source.get("left"), 0, source_width // 2, 0)
        right = clamp_int(slice_source.get("right"), 0, source_width // 2, 0)
        top = clamp_int(slice_source.get("top"), 0, source_height // 2, 0)
        bottom = clamp_int(slice_source.get("bottom"), 0, source_height // 2, 0)
        target_left = min(left, rect.width // 2)
        target_right = min(right, max(0, rect.width - target_left))
        target_top = min(top, rect.height // 2)
        target_bottom = min(bottom, max(0, rect.height - target_top))

        source_columns = [(0, left), (left, source_width - right), (source_width - right, source_width)]
        source_rows = [(0, top), (top, source_height - bottom), (source_height - bottom, source_height)]
        target_columns = [
            (0, target_left),
            (target_left, rect.width - target_right),
            (rect.width - target_right, rect.width),
        ]
        target_rows = [
            (0, target_top),
            (target_top, rect.height - target_bottom),
            (rect.height - target_bottom, rect.height),
        ]
        frame_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        for row_index, (source_y1, source_y2) in enumerate(source_rows):
            for column_index, (source_x1, source_x2) in enumerate(source_columns):
                source_rect = pygame.Rect(source_x1, source_y1, source_x2 - source_x1, source_y2 - source_y1)
                target_x1, target_x2 = target_columns[column_index]
                target_y1, target_y2 = target_rows[row_index]
                target_rect = pygame.Rect(target_x1, target_y1, target_x2 - target_x1, target_y2 - target_y1)
                if (
                    source_rect.width <= 0
                    or source_rect.height <= 0
                    or target_rect.width <= 0
                    or target_rect.height <= 0
                ):
                    continue
                segment = source.subsurface(source_rect).copy()
                if segment.get_size() != target_rect.size:
                    segment = pygame.transform.smoothscale(segment, target_rect.size)
                frame_surface.blit(segment, target_rect)

        frame_surface.set_alpha(int(round(opacity * 2.55)))
        self.screen.blit(frame_surface, rect.topleft)

    def get_game_ui_panel_frame_image(self, frame_kind: str = "panel"):
        asset_key = {
            "save": "saveSlotFrameAssetId",
            "system": "systemPanelFrameAssetId",
        }.get(frame_kind, "panelFrameAssetId")
        asset_id = str(self.game_ui_config.get(asset_key) or "").strip()
        image = self._load_image(asset_id) if asset_id else None
        if not image and frame_kind != "panel":
            fallback_asset_id = str(self.game_ui_config.get("panelFrameAssetId") or "").strip()
            image = self._load_image(fallback_asset_id) if fallback_asset_id else None
        return image

    def draw_game_ui_panel_frame(self, rect, frame_kind: str = "panel") -> None:
        self.draw_nine_slice_image(
            self.get_game_ui_panel_frame_image(frame_kind),
            rect,
            self.game_ui_config.get("panelFrameSlice"),
            int(self.game_ui_config.get("panelFrameOpacity") or 0),
        )

    def get_game_ui_button_frame_image(self, state: str = "normal"):
        asset_key = {
            "hover": "buttonHoverFrameAssetId",
            "pressed": "buttonPressedFrameAssetId",
            "disabled": "buttonDisabledFrameAssetId",
        }.get(state, "buttonFrameAssetId")
        asset_id = str(self.game_ui_config.get(asset_key) or "").strip()
        image = self._load_image(asset_id) if asset_id else None
        if not image and state != "normal":
            fallback_asset_id = str(self.game_ui_config.get("buttonFrameAssetId") or "").strip()
            image = self._load_image(fallback_asset_id) if fallback_asset_id else None
        return image

    def get_game_ui_button_state(self, rect, *, active: bool = False, disabled: bool = False) -> str:
        if disabled:
            return "disabled"
        try:
            hovered = bool(rect.collidepoint(self.pygame.mouse.get_pos()))
            pressed = bool(self.pygame.mouse.get_pressed()[0]) if hovered else False
        except Exception:
            hovered = False
            pressed = False
        if pressed:
            return "pressed"
        if hovered or active:
            return "hover"
        return "normal"

    def draw_game_ui_button_frame(self, rect, state: str = "normal") -> None:
        self.draw_nine_slice_image(
            self.get_game_ui_button_frame_image(state),
            rect,
            self.game_ui_config.get("buttonFrameSlice"),
            int(self.game_ui_config.get("buttonFrameOpacity") or 0),
        )

    def _load_sound(self, asset_id: str | None):
        if not asset_id:
            return None
        if asset_id in self.sound_cache:
            return self.sound_cache[asset_id]
        asset = self.assets_by_id.get(asset_id)
        asset_path = get_asset_runtime_path(self.bundle_dir, asset)
        if not asset_path or not self.pygame.mixer.get_init():
            self.sound_cache[asset_id] = None
            return None
        try:
            sound = self.pygame.mixer.Sound(str(asset_path))
        except Exception:
            sound = None
        self.sound_cache[asset_id] = sound
        return sound

    def get_dialog_border_radius(self, height: int) -> int:
        shape = self.dialog_box_config.get("shape")
        if shape == "square":
            return 8
        if shape == "capsule":
            return max(18, height // 2)
        return max(16, min(32, height // 6))

    def get_dialog_panel_rect(self, min_height: int) -> object:
        width_percent = self.dialog_box_config.get("widthPercent", 76) / 100
        width = max(420, min(self.width - 48, int(self.width * width_percent)))
        height = max(int(min_height), int(self.dialog_box_config.get("minHeight", 148)))
        rect = self.pygame.Rect(0, 0, width, height)
        offset_x = int(self.width * int(self.dialog_box_config.get("offsetXPercent", 0)) / 100)
        offset_y = int(self.height * int(self.dialog_box_config.get("offsetYPercent", 0)) / 100)
        anchor = str(self.dialog_box_config.get("anchor") or "bottom")
        if anchor == "top":
            rect.midtop = (self.width // 2 + offset_x, 34 + offset_y)
        elif anchor in {"center", "free"}:
            rect.center = (self.width // 2 + offset_x, self.height // 2 + offset_y)
        else:
            rect.midbottom = (self.width // 2 + offset_x, self.height - 34 + offset_y)
        rect.clamp_ip(self.pygame.Rect(12, 12, self.width - 24, self.height - 24))
        return rect

    def draw_dialog_panel(self, rect) -> None:
        pygame = self.pygame
        config = self.dialog_box_config
        radius = self.get_dialog_border_radius(rect.height)
        shadow_strength = int(config.get("shadowStrength", 0))
        if shadow_strength > 0:
            shadow_alpha = int(70 + shadow_strength * 2.2)
            shadow_surface = pygame.Surface((rect.width + 32, rect.height + 32), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow_surface,
                (0, 0, 0, min(190, shadow_alpha)),
                pygame.Rect(16, 16, rect.width, rect.height),
                border_radius=min(radius + 6, (rect.height + 12) // 2),
            )
            self.screen.blit(shadow_surface, (rect.left - 16, rect.top - 8))

        panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel_rect = panel_surface.get_rect()

        background_opacity = int(config.get("backgroundOpacity", 0))
        if background_opacity > 0:
            pygame.draw.rect(
                panel_surface,
                with_alpha(config.get("backgroundColor", COLOR_PANEL), background_opacity),
                panel_rect,
                border_radius=radius,
            )

        panel_art_id = config.get("panelAssetId")
        panel_art_opacity = int(config.get("panelAssetOpacity", 0))
        panel_art = self._load_image(panel_art_id) if panel_art_id and panel_art_opacity > 0 else None
        if panel_art:
            art_width, art_height = panel_art.get_size()
            if art_width > 0 and art_height > 0:
                if config.get("panelAssetFit") == "contain":
                    scale = min(rect.width / art_width, rect.height / art_height)
                else:
                    scale = max(rect.width / art_width, rect.height / art_height)
                scaled = pygame.transform.smoothscale(
                    panel_art,
                    (max(1, int(art_width * scale)), max(1, int(art_height * scale))),
                )
                scaled.set_alpha(int(round(panel_art_opacity * 2.55)))
                art_rect = scaled.get_rect(center=panel_rect.center)
                panel_surface.blit(scaled, art_rect)

        mask_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask_surface, (255, 255, 255, 255), mask_surface.get_rect(), border_radius=radius)
        panel_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.screen.blit(panel_surface, rect)

        border_width = int(config.get("borderWidth", 0))
        border_opacity = int(config.get("borderOpacity", 0))
        if border_width > 0 and border_opacity > 0:
            border_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(
                border_surface,
                with_alpha(config.get("borderColor", COLOR_PANEL_BORDER), border_opacity),
                border_surface.get_rect(),
                width=border_width,
                border_radius=radius,
            )
            self.screen.blit(border_surface, rect)

    def get_save_dialog_data(self) -> dict:
        return build_save_dialog_page_data(
            self.project,
            self.save_store,
            page=self.overlay_page,
            page_size=SAVE_DIALOG_PAGE_SIZE,
        )

    def get_save_dialog_slot_count(self) -> int:
        return len(self.get_save_dialog_data().get("visibleSlots") or [])

    def normalize_overlay_focus(self) -> None:
        if self.overlay_mode in {"save", "load"}:
            slot_count = self.get_save_dialog_slot_count()
            if slot_count <= 0:
                self.overlay_focus_index = 0
            else:
                self.overlay_focus_index = max(0, min(slot_count - 1, self.overlay_focus_index))
        elif self.overlay_mode == "title":
            self.title_menu_index = max(0, min(len(TITLE_MENU_ITEMS) - 1, self.title_menu_index))
        elif self.overlay_mode == "system":
            self.system_menu_index = max(0, min(len(SYSTEM_MENU_ITEMS) - 1, self.system_menu_index))

    def get_title_preview_background_asset_id(self) -> str:
        title_background_asset_id = str(self.game_ui_config.get("titleBackgroundAssetId") or "").strip()
        if title_background_asset_id:
            return title_background_asset_id
        for scene in self.scenes_by_id.values():
            for block in scene.get("blocks", []) or []:
                if str(block.get("type") or "") == "background" and block.get("assetId"):
                    return str(block.get("assetId") or "")
        return ""

    def open_title_screen(self) -> None:
        self.title_screen_active = True
        self.overlay_mode = "title"
        self.title_menu_index = 0
        self.overlay_hotspots = []
        self.current_line = None
        self.current_choices = None
        self.finished = False
        self.finished_message = ""
        self.stage_background_asset_id = self.get_title_preview_background_asset_id() or None
        self.status_message = "标题页：选择开始、续玩、读档或设置。"

    def start_story_from_title(self) -> None:
        self.title_screen_active = False
        self.overlay_mode = None
        self.overlay_hotspots = []
        self.stop_voice()
        self.stop_bgm()
        self.clear_particle_effect()
        self.clear_stage_visual_effects(include_persistent=True)
        self.current_line = None
        self.current_choices = None
        self.current_choice_index = 0
        self.finished = False
        self.finished_message = ""
        self.stage_background_asset_id = None
        self.visible_characters = {}
        self.current_bgm_asset_id = None
        self.variable_state = {
            variable.get("id"): variable.get("defaultValue")
            for variable in self.variables
            if variable.get("id")
        }
        self.current_scene_id = self.project.get("entrySceneId") or self.scene_order[0]
        if self.current_scene_id not in self.scenes_by_id:
            self.current_scene_id = self.scene_order[0]
        self.current_block_index = 0
        self.auto_resume_write_enabled = True
        self.unlock_current_chapter_replay()
        self.advance_until_pause()
        self.persist_auto_resume_snapshot()
        self.status_message = "已开始游戏。"

    def open_save_dialog(self, mode: str) -> None:
        self.overlay_mode = mode if mode in {"save", "load"} else "save"
        self.overlay_page = 0
        self.overlay_focus_index = 0
        if self.overlay_mode == "load":
            formal_slots = self.save_store.get("formalSlots") or []
            for slot_index, snapshot in enumerate(formal_slots):
                if snapshot:
                    self.overlay_page = slot_index // SAVE_DIALOG_PAGE_SIZE
                    self.overlay_focus_index = slot_index % SAVE_DIALOG_PAGE_SIZE
                    break
        self.normalize_overlay_focus()
        self.status_message = "存档面板已打开。"

    def open_system_menu(self) -> None:
        self.overlay_mode = "system"
        self.system_menu_index = 0
        self.status_message = "系统菜单已打开。"

    def open_profile_overlay(self) -> None:
        self.overlay_mode = "profile"
        self.status_message = "玩家档案已打开。"

    def open_auto_resume_overlay(self) -> None:
        self.auto_resume_snapshot = load_project_auto_resume(self.project_id)
        self.overlay_mode = "auto-resume"
        self.status_message = "续玩记录已打开。"

    def close_overlay(self, preserve_status: bool = False) -> None:
        closing_mode = self.overlay_mode
        self.overlay_hotspots = []
        self.archive_detail_entry = None
        self.archive_detail_key = None
        if self.title_screen_active and closing_mode != "title":
            self.overlay_mode = "title"
            if not preserve_status:
                self.status_message = "已返回标题页。"
            return
        self.overlay_mode = None
        if not preserve_status:
            self.status_message = "已返回游戏画面。"

    def change_save_dialog_page(self, delta: int) -> None:
        dialog_data = self.get_save_dialog_data()
        page_count = dialog_data.get("pageCount") or 1
        self.overlay_page = max(0, min(page_count - 1, self.overlay_page + delta))
        self.normalize_overlay_focus()

    def activate_overlay_slot(self, visible_slot_index: int) -> None:
        dialog_data = self.get_save_dialog_data()
        visible_slots = dialog_data.get("visibleSlots") or []
        if visible_slot_index < 0 or visible_slot_index >= len(visible_slots):
            return
        slot_index = int(visible_slots[visible_slot_index]["slotIndex"])
        if self.overlay_mode == "save":
            self.save_formal_slot(slot_index)
            self.close_overlay(preserve_status=True)
        elif self.overlay_mode == "load":
            snapshot = (self.save_store.get("formalSlots") or [None] * self.formal_save_slot_count)[slot_index]
            if not snapshot:
                self.status_message = f"正式存档 {slot_index + 1} 还是空的。"
                return
            self.load_formal_slot(slot_index)
            self.close_overlay(preserve_status=True)

    def restart_story(self) -> None:
        self.record_player_return_to_start()
        self.start_story_from_title()
        self.status_message = "已回到开头。"

    def activate_system_menu_item(self, item_key: str) -> bool:
        if item_key == "continue":
            self.close_overlay()
            return True
        if item_key == "archives":
            self.open_archive_overlay()
            return True
        if item_key == "profile":
            self.open_profile_overlay()
            return True
        if item_key == "auto-resume":
            self.open_auto_resume_overlay()
            return True
        if item_key == "save":
            self.open_save_dialog("save")
            return True
        if item_key == "load":
            self.open_save_dialog("load")
            return True
        if item_key == "settings":
            self.open_settings_overlay()
            return True
        if item_key == "quick-save":
            self.save_quick()
            self.close_overlay(preserve_status=True)
            return True
        if item_key == "quick-load":
            self.load_quick()
            self.close_overlay(preserve_status=True)
            return True
        if item_key == "restart":
            self.restart_story()
            return True
        if item_key == "exit":
            return False
        return True

    def get_title_menu_items(self) -> list[dict]:
        self.auto_resume_snapshot = load_project_auto_resume(self.project_id)
        formal_slots = self.save_store.get("formalSlots") or []
        filled_formal_count = sum(1 for item in formal_slots if item)
        menu_items = []
        for item_key, item_label in TITLE_MENU_ITEMS:
            enabled = True
            subtitle = ""
            if item_key == "start":
                subtitle = "从入口场景开始新的游玩。"
            elif item_key == "resume":
                enabled = self.auto_resume_snapshot is not None
                subtitle = (
                    f"{self.auto_resume_snapshot.get('sceneName') or '未命名场景'} · {format_snapshot_saved_at(self.auto_resume_snapshot.get('savedAt'))}"
                    if self.auto_resume_snapshot
                    else "推进一次剧情后会自动生成续玩记录。"
                )
            elif item_key == "load":
                subtitle = f"正式存档 {filled_formal_count}/{self.formal_save_slot_count}。"
            elif item_key == "settings":
                subtitle = "主题、全屏、文字速度和音量。"
            elif item_key == "archives":
                subtitle = "章节、音乐、CG、角色、结局和成就。"
            elif item_key == "exit":
                subtitle = "关闭原生 Runtime。"
            menu_items.append({"key": item_key, "label": item_label, "subtitle": subtitle, "enabled": enabled})
        return menu_items

    def activate_title_menu_item(self, item_key: str) -> bool:
        if item_key == "start":
            self.start_story_from_title()
            return True
        if item_key == "resume":
            if not self.auto_resume_snapshot:
                self.status_message = "当前还没有续玩记录。"
                return True
            self.load_auto_resume_snapshot()
            return True
        if item_key == "load":
            self.open_save_dialog("load")
            return True
        if item_key == "settings":
            self.open_settings_overlay()
            return True
        if item_key == "archives":
            self.open_archive_overlay()
            return True
        if item_key == "exit":
            return False
        return True

    def open_archive_overlay(self, archive_key: str | None = None) -> None:
        safe_key = archive_key if archive_key in ARCHIVE_MENU_ITEMS else self.current_archive_key or "chapters"
        self.overlay_mode = "archives"
        self.current_archive_key = safe_key
        self.archive_selection_index = 0
        entries = self.get_archive_entries(safe_key)
        for index, entry in enumerate(entries):
            if entry.get("unlocked"):
                self.archive_selection_index = index
                break
        self.status_message = f"{ARCHIVE_MENU_ITEMS.get(safe_key, '资料馆')} 已打开。"

    def open_settings_overlay(self) -> None:
        self.overlay_mode = "settings"
        self.settings_menu_index = 0
        self.status_message = "体验设置已打开。"

    def adjust_runtime_setting(self, setting_key: str, direction: int) -> None:
        if setting_key == "themeMode":
            current = str(self.runtime_settings.get("themeMode") or "auto")
            options = list(RUNTIME_THEME_MODES)
            current_index = options.index(current) if current in options else 0
            self.runtime_settings["themeMode"] = options[(current_index + direction) % len(options)]
        elif setting_key == "displayMode":
            current = str(self.runtime_settings.get("displayMode") or "windowed")
            options = list(RUNTIME_DISPLAY_MODES)
            current_index = options.index(current) if current in options else 0
            self.runtime_settings["displayMode"] = options[(current_index + direction) % len(options)]
        elif setting_key == "textSpeed":
            current = str(self.runtime_settings.get("textSpeed") or "normal")
            options = list(TEXT_SPEED_PRESETS.keys())
            current_index = options.index(current) if current in options else 0
            self.runtime_settings["textSpeed"] = options[(current_index + direction) % len(options)]
            if self.current_line and not self.is_current_line_fully_visible():
                self.start_current_line_display(self.current_line_full_text)
        elif setting_key in {"masterVolume", "bgmVolume", "sfxVolume", "voiceVolume"}:
            current_value = int(self.runtime_settings.get(setting_key) or DEFAULT_RUNTIME_PLAYER_SETTINGS[setting_key])
            self.runtime_settings[setting_key] = clamp_int(current_value + direction * 5, 0, 100, current_value)
        self.runtime_settings = sanitize_runtime_player_settings(self.runtime_settings)
        self.persist_runtime_settings()
        self.apply_runtime_settings()
        self.status_message = "体验设置已更新。"

    def get_setting_value_label(self, setting_key: str) -> str:
        if setting_key == "themeMode":
            label_map = {"auto": "自动", "light": "浅色", "dark": "深色"}
            selected = str(self.runtime_settings.get("themeMode") or "auto")
            active = self.get_active_theme_mode()
            return f"{label_map.get(selected, selected)}（当前：{label_map.get(active, active)}）"
        if setting_key == "displayMode":
            label_map = {"windowed": "窗口", "fullscreen": "全屏"}
            selected = str(self.runtime_settings.get("displayMode") or "windowed")
            return label_map.get(selected, selected)
        if setting_key == "textSpeed":
            speed_key = str(self.runtime_settings.get("textSpeed") or "normal")
            return TEXT_SPEED_LABELS.get(speed_key, speed_key)
        return f"{int(self.runtime_settings.get(setting_key) or 0)}%"

    def activate_archive_entry(self, entry: dict | None) -> bool:
        if not entry:
            return True
        if not entry.get("unlocked"):
            self.status_message = "当前条目还没有解锁。"
            return True
        if self.current_archive_key == "chapters":
            first_scene_id = str(entry.get("firstSceneId") or "")
            if not first_scene_id:
                self.status_message = "这章还没有可回放的起点场景。"
                return True
            self.stop_voice()
            self.current_choices = None
            self.current_line = None
            self.finished = False
            self.finished_message = ""
            self.title_screen_active = False
            self.set_scene(first_scene_id)
            self.close_overlay(preserve_status=True)
            self.advance_until_pause()
            self.auto_resume_write_enabled = True
            self.persist_auto_resume_snapshot()
            self.status_message = f"已从章节开头进入：{entry.get('name') or '未命名章节'}"
            return True
        if self.current_archive_key == "music":
            self.play_bgm(str(entry.get("id") or ""), loop=True)
            self.status_message = f"正在试听：{entry.get('name') or '未命名曲目'}"
            return True
        if self.current_archive_key == "gallery":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "locations":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "characters":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "narrations":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "relations":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "voices":
            voice_asset_id = str(entry.get("voiceAssetId") or "")
            if voice_asset_id:
                self.play_voice(voice_asset_id)
                self.status_message = f"正在回放语音：{entry.get('name') or '未命名条目'}"
            else:
                self.status_message = "这个条目当前没有可回放语音。"
            return True
        if self.current_archive_key == "endings":
            scene_id = str(entry.get("id") or "")
            if not scene_id:
                self.status_message = "这个结局当前没有可回放的场景。"
                return True
            self.stop_voice()
            self.current_choices = None
            self.current_line = None
            self.finished = False
            self.finished_message = ""
            self.title_screen_active = False
            self.set_scene(scene_id)
            self.close_overlay(preserve_status=True)
            self.advance_until_pause()
            self.auto_resume_write_enabled = True
            self.persist_auto_resume_snapshot()
            self.status_message = f"已进入结局回放：{entry.get('name') or '未命名结局'}"
            return True
        if self.current_archive_key == "achievements":
            self.open_archive_detail(entry)
            return True
        return True

    def open_archive_detail(self, entry: dict) -> None:
        self.archive_detail_key = self.current_archive_key
        self.archive_detail_entry = dict(entry)
        self.overlay_mode = "archive-detail"
        self.status_message = f"正在查看：{entry.get('name') or '资料馆条目'}"

    def close_archive_detail(self) -> None:
        self.overlay_mode = "archives"
        self.archive_detail_entry = None
        self.archive_detail_key = None
        self.status_message = "已返回资料馆。"

    def get_chapter_for_scene(self, scene_id: str | None) -> dict | None:
        safe_scene_id = str(scene_id or "").strip()
        if not safe_scene_id:
            return None
        for chapter in self.chapters:
            for scene in chapter.get("scenes") or []:
                if str(scene.get("id") or "") == safe_scene_id:
                    return chapter
        return None

    def unlock_current_chapter_replay(self) -> None:
        chapter = self.get_chapter_for_scene(self.current_scene_id)
        chapter_id = str((chapter or {}).get("chapterId") or "")
        if chapter_id:
            self.unlock_archive_entry("chapterReplayUnlocked", chapter_id)

    def get_current_scene(self) -> dict | None:
        return self.scenes_by_id.get(self.current_scene_id)

    def get_current_scene_name(self) -> str:
        return str((self.get_current_scene() or {}).get("name") or self.current_scene_id or "未命名场景")

    def get_current_line_preview(self) -> str:
        if self.current_line and self.current_line.get("text"):
            return str(self.current_line["text"]).strip()
        if self.current_choices:
            return "当前停在选项卡。"
        if self.finished:
            return self.finished_message or "剧情已经结束。"
        return ""

    def build_save_snapshot(self, kind: str) -> dict:
        return {
            "kind": kind,
            "savedAt": now_iso(),
            "sceneId": self.current_scene_id,
            "sceneName": self.get_current_scene_name(),
            "blockIndex": self.current_block_index,
            "variableState": dict(self.variable_state),
            "stageBackgroundAssetId": self.stage_background_asset_id,
            "visibleCharacters": dict(self.visible_characters),
            "currentBgmAssetId": self.current_bgm_asset_id,
            "finished": self.finished,
            "finishedMessage": self.finished_message,
            "summaryText": self.get_current_line_preview()[:96],
            "particleEffect": dict(self.active_particle_effect) if self.active_particle_effect else None,
            "visualEffects": {
                "screenFade": dict(self.screen_fade_effect) if self.screen_fade_effect else None,
                "cameraZoom": dict(self.camera_zoom_effect) if self.camera_zoom_effect else None,
                "cameraPan": dict(self.camera_pan_effect) if self.camera_pan_effect else None,
                "screenFilter": dict(self.screen_filter_effect) if self.screen_filter_effect else None,
                "depthBlur": dict(self.depth_blur_effect) if self.depth_blur_effect else None,
            },
        }

    def persist_save_store(self) -> None:
        write_project_save_store(self.project_id, self.save_store)

    def save_quick(self) -> None:
        self.save_store["quickSave"] = self.build_save_snapshot("quick")
        self.persist_save_store()
        self.status_message = f"快速存档已写入：{self.save_file_path.name}"

    def load_quick(self) -> None:
        snapshot = self.save_store.get("quickSave")
        if not snapshot:
            self.status_message = "当前还没有快速存档。"
            return
        self.restore_from_snapshot(snapshot)
        self.persist_auto_resume_snapshot()
        self.status_message = f"已读入快速存档：{snapshot.get('sceneName') or '未命名场景'}"

    def save_formal_slot(self, slot_index: int) -> None:
        if slot_index < 0 or slot_index >= self.formal_save_slot_count:
            return
        self.save_store["formalSlots"][slot_index] = self.build_save_snapshot("formal")
        self.persist_save_store()
        self.status_message = f"正式存档 {slot_index + 1} 已写入：{self.save_file_path.name}"

    def load_formal_slot(self, slot_index: int) -> None:
        if slot_index < 0 or slot_index >= self.formal_save_slot_count:
            return
        snapshot = (self.save_store.get("formalSlots") or [None] * self.formal_save_slot_count)[slot_index]
        if not snapshot:
            self.status_message = f"正式存档 {slot_index + 1} 还是空的。"
            return
        self.restore_from_snapshot(snapshot)
        self.persist_auto_resume_snapshot()
        self.status_message = f"已读入正式存档 {slot_index + 1}：{snapshot.get('sceneName') or '未命名场景'}"

    def restore_from_snapshot(self, snapshot: dict) -> None:
        self.title_screen_active = False
        self.overlay_mode = None
        self.auto_resume_write_enabled = True
        self.stop_voice()
        self.current_line = None
        self.current_choices = None
        self.current_choice_index = 0
        self.finished = bool(snapshot.get("finished"))
        self.finished_message = str(snapshot.get("finishedMessage") or "")
        scene_id = str(snapshot.get("sceneId") or self.project.get("entrySceneId") or self.scene_order[0])
        self.current_scene_id = scene_id if scene_id in self.scenes_by_id else self.scene_order[0]
        self.unlock_current_chapter_replay()
        self.current_block_index = int(snapshot.get("blockIndex") or 0)
        restored_variable_state = {
            variable.get("id"): variable.get("defaultValue")
            for variable in self.variables
            if variable.get("id")
        }
        restored_variable_state.update(dict(snapshot.get("variableState") or {}))
        self.variable_state = restored_variable_state
        self.stage_background_asset_id = snapshot.get("stageBackgroundAssetId")
        self.visible_characters = dict(snapshot.get("visibleCharacters") or {})
        self.current_bgm_asset_id = None
        self.clear_particle_effect()
        self.clear_stage_visual_effects(include_persistent=True)

        bgm_asset_id = snapshot.get("currentBgmAssetId")
        if bgm_asset_id:
            self.play_bgm(bgm_asset_id, loop=True)
        else:
            self.stop_bgm()

        particle_effect = snapshot.get("particleEffect")
        if particle_effect:
            self.set_particle_effect(particle_effect)

        visual_effects = snapshot.get("visualEffects") or {}
        self.screen_fade_effect = visual_effects.get("screenFade")
        self.camera_zoom_effect = visual_effects.get("cameraZoom")
        self.camera_pan_effect = visual_effects.get("cameraPan")
        self.screen_filter_effect = visual_effects.get("screenFilter")
        self.depth_blur_effect = visual_effects.get("depthBlur")

        if self.finished:
            self.persist_auto_resume_snapshot()
            return
        self.hydrate_pause_from_current_block()
        self.persist_auto_resume_snapshot()

    def set_scene(self, scene_id: str | None) -> None:
        if scene_id and scene_id in self.scenes_by_id:
            self.current_scene_id = scene_id
            self.current_block_index = 0
            self.unlock_current_chapter_replay()
            return
        self.finished = True
        self.finished_message = "剧情已经结束。"

    def clear_particle_effect(self) -> None:
        self.active_particle_effect = None
        self.particle_items = []

    def clear_stage_visual_effects(self, include_persistent: bool = False) -> None:
        self.screen_shake_effect = None
        self.screen_flash_effect = None
        if include_persistent:
            self.screen_fade_effect = None
            self.camera_zoom_effect = None
            self.camera_pan_effect = None
            self.screen_filter_effect = None
            self.depth_blur_effect = None

    def apply_stage_visual_effect_block(self, block: dict) -> None:
        config = normalize_native_visual_effect_block(block)
        block_type = config.get("type")
        if block_type == "screen_shake":
            self.screen_shake_effect = {
                **config,
                "remaining": get_effect_duration_seconds(config.get("duration")),
                "durationSeconds": get_effect_duration_seconds(config.get("duration")),
            }
        elif block_type == "screen_flash":
            self.screen_flash_effect = {
                **config,
                "remaining": get_effect_duration_seconds(config.get("duration")),
                "durationSeconds": get_effect_duration_seconds(config.get("duration")),
            }
        elif block_type == "screen_fade":
            self.screen_fade_effect = None if config.get("action") == "fade_in" else config
        elif block_type == "camera_zoom":
            self.camera_zoom_effect = None if config.get("action") == "reset" else config
        elif block_type == "camera_pan":
            self.camera_pan_effect = None if config.get("target") == "center" else config
        elif block_type == "screen_filter":
            self.screen_filter_effect = None if config.get("action") == "clear" else config
        elif block_type == "depth_blur":
            self.depth_blur_effect = None if config.get("action") == "clear" else config
        self.status_message = f"演出已应用：{get_block_label(str(block_type or ''))}"

    def set_particle_effect(self, effect: dict | None) -> None:
        config = normalize_native_particle_effect_config(effect)
        if config["action"] == "stop":
            self.clear_particle_effect()
            return
        self.active_particle_effect = config
        self.particle_items = build_native_particle_items(config, self.width, self.height)

    def update_particle_effect(self, dt_seconds: float) -> None:
        if not self.active_particle_effect or not self.particle_items:
            return
        config = self.active_particle_effect
        preset = str(config.get("preset") or "snow")
        upward = preset in {"bubbles", "smoke", "flame", "stardust", "glyphs"}
        padding = max(32.0, float(config.get("sizeMax") or 20) * 2.0)
        for index, item in enumerate(self.particle_items):
            item["life"] = max(0.0, float(item.get("life") or 0.0) - dt_seconds)
            item["rotation"] = float(item.get("rotation") or 0.0) + float(item.get("spin") or 0.0) * dt_seconds
            wobble = math.sin(self.runtime_elapsed_seconds * 1.8 + float(item.get("wobblePhase") or 0.0)) * float(item.get("wobble") or 0.0)
            item["x"] = float(item.get("x") or 0.0) + float(item.get("vx") or 0.0) * dt_seconds + wobble * dt_seconds
            item["y"] = float(item.get("y") or 0.0) + float(item.get("vy") or 0.0) * dt_seconds
            out_of_bounds = (
                item["x"] < -padding
                or item["x"] > self.width + padding
                or item["y"] < -padding
                or item["y"] > self.height + padding
            )
            if item["life"] <= 0 or out_of_bounds:
                replacement = build_native_particle_item(config, self.width, self.height)
                if upward:
                    replacement["y"] = random.uniform(self.height * 0.5, self.height + padding * 0.5)
                else:
                    replacement["y"] = random.uniform(-self.height * 0.2, 0.0)
                self.particle_items[index] = replacement

    def update_stage_visual_effects(self, dt_seconds: float) -> None:
        for attr_name in ("screen_shake_effect", "screen_flash_effect"):
            effect = getattr(self, attr_name)
            if not effect:
                continue
            remaining = max(0.0, float(effect.get("remaining") or 0.0) - dt_seconds)
            effect["remaining"] = remaining
            if remaining <= 0:
                setattr(self, attr_name, None)

    def render_particle_shape(self, surface, shape: str, color: tuple[int, int, int], alpha: int, size: int) -> None:
        draw_color = (*color, max(0, min(255, alpha)))
        center = size // 2
        radius = max(1, size // 2 - 1)
        if shape == "rain":
            self.pygame.draw.line(surface, draw_color, (center, 1), (center + max(1, size // 4), size - 2), max(1, size // 6))
        elif shape == "petal":
            self.pygame.draw.ellipse(surface, draw_color, (1, center // 2, max(2, size - 2), max(2, size // 2)))
        elif shape == "bubble":
            self.pygame.draw.circle(surface, draw_color, (center, center), radius, max(1, size // 8))
            self.pygame.draw.circle(surface, (*color, max(0, min(255, alpha // 2))), (max(1, center - radius // 3), max(1, center - radius // 3)), max(1, radius // 5))
        elif shape == "confetti":
            self.pygame.draw.rect(surface, draw_color, (1, 1, max(2, size - 2), max(2, size // 2)), border_radius=max(1, size // 8))
        elif shape == "smoke":
            self.pygame.draw.circle(surface, draw_color, (center, center), radius)
        elif shape == "flame":
            points = [(center, 1), (size - 2, size - 3), (center, size - 2), (2, size - 3)]
            self.pygame.draw.polygon(surface, draw_color, points)
        elif shape == "ember":
            self.pygame.draw.circle(surface, draw_color, (center, center), radius)
        elif shape == "spark":
            self.pygame.draw.line(surface, draw_color, (center, 0), (center, size), max(1, size // 7))
            self.pygame.draw.line(surface, draw_color, (0, center), (size, center), max(1, size // 7))
        elif shape == "star":
            self.pygame.draw.line(surface, draw_color, (center, 0), (center, size), max(1, size // 8))
            self.pygame.draw.line(surface, draw_color, (0, center), (size, center), max(1, size // 8))
            self.pygame.draw.line(surface, draw_color, (2, 2), (size - 2, size - 2), max(1, size // 9))
            self.pygame.draw.line(surface, draw_color, (size - 2, 2), (2, size - 2), max(1, size // 9))
        elif shape == "glyph":
            rect = self.pygame.Rect(2, 2, max(2, size - 4), max(2, size - 4))
            self.pygame.draw.rect(surface, draw_color, rect, max(1, size // 8), border_radius=max(1, size // 6))
            self.pygame.draw.line(surface, draw_color, (rect.left + 3, rect.centery), (rect.right - 3, rect.centery), max(1, size // 10))
        else:
            self.pygame.draw.circle(surface, draw_color, (center, center), radius)

    def render_particle_effect(self, target=None) -> None:
        if not self.active_particle_effect or not self.particle_items:
            return
        target = target or self.screen
        config = self.active_particle_effect
        asset_id = str(config.get("assetId") or "")
        particle_image = self._load_image(asset_id) if asset_id else None
        for item in self.particle_items:
            progress = 1.0 - (float(item.get("life") or 0.0) / max(0.001, float(item.get("maxLife") or 1.0)))
            size = max(2, int(round(float(item.get("size") or 4.0))))
            alpha = int(round(255 * (0.15 + (1.0 - progress) * 0.85)))
            color = mix_rgb(
                tuple(config.get("color") or (255, 255, 255)),
                tuple(config.get("accentColor") or (214, 238, 255)),
                float(item.get("colorMix") or 0.0) * (0.5 + progress * 0.5),
            )
            if particle_image:
                image = self.pygame.transform.smoothscale(particle_image, (size, size))
                if image.get_flags() & self.pygame.SRCALPHA:
                    image = image.copy()
                image.set_alpha(alpha)
            else:
                image = self.pygame.Surface((size, size), self.pygame.SRCALPHA)
                self.render_particle_shape(image, str(config.get("shape") or "glow"), color, alpha, size)
            rotation = float(item.get("rotation") or 0.0)
            if abs(rotation) > 0.01:
                image = self.pygame.transform.rotozoom(image, -rotation, 1.0)
            rect = image.get_rect(center=(int(item.get("x") or 0), int(item.get("y") or 0)))
            target.blit(image, rect)

    def hydrate_pause_from_current_block(self) -> None:
        scene = self.get_current_scene()
        blocks = (scene or {}).get("blocks", []) or []
        if self.current_block_index >= len(blocks):
            self.handle_scene_finished(scene)
            return

        block = blocks[self.current_block_index]
        block_type = str(block.get("type") or "").strip()
        if block_type == "choice":
            self.current_choices = block.get("options", []) or []
            self.current_choice_index = 0
            return
        if block_type in {"dialogue", "narration"}:
            line_text = str(block.get("text") or "")
            self.current_line = {
                "type": block_type,
                "speakerId": block.get("speakerId"),
                "text": line_text,
                "voiceAssetId": block.get("voiceAssetId"),
                "blockLabel": get_block_label(block_type),
            }
            self.sync_archive_progress_for_pause(scene, block, self.current_block_index)
            self.start_current_line_display(line_text)
            if block_type == "dialogue":
                self.sync_expression_for_dialogue(block)
                self.play_voice(block.get("voiceAssetId"))
            else:
                self.stop_voice()
            return
        self.advance_until_pause()

    def advance_until_pause(self) -> None:
        self.current_line = None
        self.current_choices = None

        while not self.finished:
            scene = self.get_current_scene()
            if not scene:
                self.finished = True
                self.finished_message = "当前路线没有有效场景。"
                return

            blocks = scene.get("blocks", []) or []
            if self.current_block_index >= len(blocks):
                self.handle_scene_finished(scene)
                return

            block = blocks[self.current_block_index]
            block_type = str(block.get("type") or "").strip()

            if block_type == "background":
                self.stage_background_asset_id = block.get("assetId")
                background_asset = self.assets_by_id.get(self.stage_background_asset_id) or {}
                if background_asset.get("type") == "cg":
                    self.unlock_archive_entry("cgUnlocked", self.stage_background_asset_id)
                elif background_asset.get("type") == "background":
                    self.unlock_archive_entry("locationUnlocked", self.stage_background_asset_id)
                self.current_block_index += 1
                continue

            if block_type == "character_show":
                character_id = block.get("characterId")
                if character_id:
                    self.unlock_archive_entry("characterUnlocked", character_id)
                    self.visible_characters[character_id] = {
                        "expressionId": block.get("expressionId"),
                        "position": block.get("position"),
                    }
                self.current_block_index += 1
                continue

            if block_type == "character_hide":
                character_id = block.get("characterId")
                if character_id:
                    self.visible_characters.pop(character_id, None)
                self.current_block_index += 1
                continue

            if block_type == "music_play":
                self.play_bgm(block.get("assetId"), loop=bool(block.get("loop", True)))
                self.current_block_index += 1
                continue

            if block_type == "music_stop":
                self.stop_bgm()
                self.current_block_index += 1
                continue

            if block_type == "particle_effect":
                if str(block.get("action") or "start").strip() == "stop":
                    self.clear_particle_effect()
                    self.status_message = "粒子特效已停止。"
                else:
                    self.set_particle_effect(block)
                    self.status_message = f"粒子特效已启动：{self.active_particle_effect.get('preset') if self.active_particle_effect else 'snow'}"
                self.current_block_index += 1
                continue

            if block_type in {"screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur"}:
                self.apply_stage_visual_effect_block(block)
                self.current_block_index += 1
                continue

            if block_type == "sfx_play":
                self.play_sfx(block.get("assetId"))
                self.current_block_index += 1
                continue

            if block_type == "video_play":
                asset_id = str(block.get("assetId") or "")
                asset = self.assets_by_id.get(asset_id) or {}
                asset_path = get_asset_runtime_path(self.bundle_dir, asset)
                start_time = normalize_video_time_seconds(block.get("startTimeSeconds"))
                end_time = normalize_video_time_seconds(block.get("endTimeSeconds"))
                if end_time <= start_time:
                    end_time = 0.0
                text = self.build_native_video_prompt(block, asset, asset_path)
                self.current_line = {
                    "type": block_type,
                    "speakerId": None,
                    "speakerName": "视频",
                    "text": text,
                    "voiceAssetId": None,
                    "videoAssetId": asset_id,
                    "videoAssetPath": str(asset_path) if asset_path else "",
                    "videoTitle": str(block.get("title") or asset.get("name") or "视频播放"),
                    "videoFileName": asset_path.name if asset_path else "",
                    "videoStartTimeSeconds": start_time,
                    "videoEndTimeSeconds": end_time,
                    "videoClipLabel": build_video_clip_label(start_time, end_time),
                    "videoFit": str(block.get("fit") or "contain"),
                    "videoVolume": clamp_int(block.get("volume"), 0, 100, 100),
                    "videoSkippable": bool(block.get("skippable", True)),
                    "videoPreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
                    "videoOpened": False,
                    "blockLabel": get_block_label(block_type),
                }
                self.stop_voice()
                self.start_current_line_display(text)
                self.reveal_current_line_immediately()
                self.status_message = "视频卡片：按 V 播放，Enter 继续"
                return

            if block_type == "credits_roll":
                lines = block.get("lines") if isinstance(block.get("lines"), list) else []
                credits_text = "\n".join(str(line) for line in lines[:12] if str(line).strip())
                text = (
                    f"{str(block.get('title') or 'STAFF')}\n"
                    f"{str(block.get('subtitle') or '').strip()}\n\n"
                    f"{credits_text or '感谢游玩。'}"
                ).strip()
                self.current_line = {
                    "type": block_type,
                    "speakerId": None,
                    "speakerName": "片尾字幕",
                    "text": text,
                    "voiceAssetId": None,
                    "blockLabel": get_block_label(block_type),
                }
                self.stop_voice()
                self.start_current_line_display(text)
                self.reveal_current_line_immediately()
                self.status_message = "片尾字幕：按继续推进"
                return

            if block_type == "variable_set":
                self.apply_variable_set(block)
                self.current_block_index += 1
                continue

            if block_type == "variable_add":
                self.apply_variable_add(block)
                self.current_block_index += 1
                continue

            if block_type == "jump":
                self.set_scene(block.get("targetSceneId"))
                continue

            if block_type == "condition":
                self.resolve_condition(block)
                continue

            if block_type == "choice":
                options = block.get("options", []) or []
                self.current_choices = options
                self.current_choice_index = 0
                self.status_message = f"当前为选项卡：{len(options)} 个分支"
                return

            if block_type in {"dialogue", "narration"}:
                line_text = str(block.get("text") or "")
                self.current_line = {
                    "type": block_type,
                    "speakerId": block.get("speakerId"),
                    "text": line_text,
                    "voiceAssetId": block.get("voiceAssetId"),
                    "blockLabel": get_block_label(block_type),
                }
                self.sync_archive_progress_for_pause(scene, block, self.current_block_index)
                self.start_current_line_display(line_text)
                if block_type == "dialogue":
                    self.sync_expression_for_dialogue(block)
                    self.play_voice(block.get("voiceAssetId"))
                else:
                    self.stop_voice()
                self.status_message = f"当前卡片：{get_block_label(block_type)}"
                return

            self.current_block_index += 1

    def sync_expression_for_dialogue(self, block: dict) -> None:
        speaker_id = block.get("speakerId")
        if not speaker_id:
            return
        self.unlock_archive_entry("characterUnlocked", speaker_id)
        character = self.characters_by_id.get(speaker_id)
        if not character:
            return
        existing = self.visible_characters.get(speaker_id, {})
        self.visible_characters[speaker_id] = {
            "expressionId": block.get("expressionId") or existing.get("expressionId") or "expr_default",
            "position": existing.get("position") or character.get("defaultPosition") or "center",
        }

    def play_bgm(self, asset_id: str | None, loop: bool = True) -> None:
        if not self.pygame.mixer.get_init():
            return
        if asset_id == self.current_bgm_asset_id:
            return
        asset = self.assets_by_id.get(asset_id)
        asset_path = get_asset_runtime_path(self.bundle_dir, asset)
        if not asset_path:
            self.current_bgm_asset_id = None
            return
        if asset and asset.get("type") == "bgm":
            self.unlock_archive_entry("bgmUnlocked", asset_id)
        try:
            self.pygame.mixer.music.load(str(asset_path))
            self.pygame.mixer.music.set_volume(self.get_effective_volume("bgmVolume"))
            self.pygame.mixer.music.play(-1 if loop else 0)
            self.current_bgm_asset_id = asset_id
        except Exception:
            self.current_bgm_asset_id = None

    def stop_bgm(self) -> None:
        if self.pygame.mixer.get_init():
            self.pygame.mixer.music.stop()
        self.current_bgm_asset_id = None

    def play_sfx(self, asset_id: str | None) -> None:
        sound = self._load_sound(asset_id)
        if sound:
            try:
                sound.set_volume(self.get_effective_volume("sfxVolume"))
                sound.play()
            except Exception:
                return

    def play_voice(self, asset_id: str | None) -> None:
        self.stop_voice()
        sound = self._load_sound(asset_id)
        if not sound:
            return
        try:
            sound.set_volume(self.get_effective_volume("voiceVolume"))
            self.current_voice_channel = sound.play()
        except Exception:
            self.current_voice_channel = None

    def stop_voice(self) -> None:
        if self.current_voice_channel:
            try:
                self.current_voice_channel.stop()
            except Exception:
                pass
        self.current_voice_channel = None

    def build_native_video_prompt(self, block: dict, asset: dict, asset_path: Path | None) -> str:
        title = str(block.get("title") or asset.get("name") or "视频播放")
        start_time = normalize_video_time_seconds(block.get("startTimeSeconds"))
        end_time = normalize_video_time_seconds(block.get("endTimeSeconds"))
        if end_time <= start_time:
            end_time = 0.0
        lines = [
            title,
            "",
            "原生 Runtime Preview 会显示影院式视频卡片，并用系统默认视频播放器桥接这段视频。",
        ]
        if asset_path:
            lines.extend(
                [
                    f"文件：{asset_path.name}",
                    f"操作：按 V 播放/重新打开视频；播放结束后回到游戏窗口，按 Enter 或 Space 继续。",
                ]
            )
        else:
            lines.extend(
                [
                    "视频文件没有被找到，可能是素材缺失或导出包不完整。",
                    "建议回到编辑器重新导出，或改用网页包 / NW.js 桌面包验证视频。",
                ]
            )

        has_clip_range = start_time > 0 or end_time > 0
        if has_clip_range:
            lines.append(
                f"剪辑提示：编辑器设置了 {build_video_clip_label(start_time, end_time)}；"
                "系统播放器桥接不会强制裁切，正式 OP/ED 建议优先用网页/NW.js 包或预先导出剪辑后的视频。"
            )
        if not bool(block.get("skippable", True)):
            lines.append("不可跳过提示：需要先按 V 唤起视频，再回到窗口按 Enter 确认继续。")
        lines.append("如果安装可选 OpenCV 依赖，视频卡片会尝试显示剪辑起点附近的一帧预览。")
        return "\n".join(lines)

    def get_video_preview_cache_key(self, line: dict) -> str:
        video_path_value = str(line.get("videoAssetPath") or "").strip()
        if not video_path_value:
            return ""
        start_time = normalize_video_time_seconds(line.get("videoStartTimeSeconds"))
        return f"{Path(video_path_value).resolve()}::{start_time:.3f}"

    def get_video_preview_frame_result(self, line: dict) -> dict:
        cache_key = self.get_video_preview_cache_key(line)
        if not cache_key:
            return {"surface": None, "status": "视频文件缺失"}
        if cache_key not in self.video_preview_frame_cache:
            video_path_value = str(line.get("videoAssetPath") or "").strip()
            start_time = normalize_video_time_seconds(line.get("videoStartTimeSeconds"))
            surface, status = load_opencv_video_frame_surface(self.pygame, Path(video_path_value), start_time)
            self.video_preview_frame_cache[cache_key] = {"surface": surface, "status": status}
        return self.video_preview_frame_cache[cache_key]

    def open_current_video(self) -> None:
        if not self.current_line or self.current_line.get("type") != "video_play":
            return
        video_path_value = str(self.current_line.get("videoAssetPath") or "").strip()
        if not video_path_value:
            self.status_message = "当前视频文件不存在，无法打开。"
            return
        success, message = open_external_video(Path(video_path_value))
        self.current_line["videoOpened"] = bool(success)
        self.status_message = message
        self.reveal_current_line_immediately()

    def can_advance_current_line(self) -> bool:
        if not self.current_line or self.current_line.get("type") != "video_play":
            return True
        requires_confirmation = (
            self.current_line.get("videoSkippable") is False
            and bool(self.current_line.get("videoAssetPath"))
            and not bool(self.current_line.get("videoOpened"))
        )
        if not requires_confirmation:
            return True
        self.status_message = "这段视频标记为不可跳过，请先按 V 播放，再回到窗口确认继续。"
        return False

    def advance_current_line_if_allowed(self) -> None:
        if self.can_advance_current_line():
            self.advance_dialogue()

    def handle_video_card_mouse_event(self, event) -> bool:
        for target in self.video_hotspots:
            if not target["rect"].collidepoint(event.pos):
                continue
            if target.get("disabled"):
                self.can_advance_current_line()
                return True
            if target.get("kind") == "play-video":
                self.open_current_video()
                return True
            if target.get("kind") == "continue-video":
                self.advance_current_line_if_allowed()
                return True
        return True

    def apply_variable_set(self, block: dict) -> None:
        variable_id = block.get("variableId")
        if not variable_id:
            return
        self.variable_state[variable_id] = block.get("value")

    def apply_variable_add(self, block: dict) -> None:
        variable_id = block.get("variableId")
        if not variable_id:
            return
        current = self.variable_state.get(variable_id, 0)
        try:
            current_number = float(current)
        except (TypeError, ValueError):
            current_number = 0.0
        try:
            delta = float(block.get("value", 0))
        except (TypeError, ValueError):
            delta = 0.0
        next_value = current_number + delta
        if int(next_value) == next_value:
            next_value = int(next_value)
        self.variable_state[variable_id] = next_value

    def evaluate_operator(self, current_value, operator: str, target_value) -> bool:
        if operator in {"==", "="}:
            return current_value == target_value
        if operator == "!=":
            return current_value != target_value
        try:
            left = float(current_value)
            right = float(target_value)
        except (TypeError, ValueError):
            left = str(current_value)
            right = str(target_value)
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        return False

    def evaluate_when(self, conditions: list[dict]) -> bool:
        if not conditions:
            return False
        for condition in conditions:
            variable_id = condition.get("variableId")
            operator = str(condition.get("operator") or "==")
            expected_value = condition.get("value")
            current_value = self.variable_state.get(variable_id)
            if not self.evaluate_operator(current_value, operator, expected_value):
                return False
        return True

    def resolve_condition(self, block: dict) -> None:
        for branch in block.get("branches", []) or []:
            if self.evaluate_when(branch.get("when", []) or []):
                self.set_scene(branch.get("gotoSceneId"))
                return
        self.set_scene(block.get("elseGotoSceneId"))

    def apply_choice_effect(self, effect: dict) -> None:
        effect_type = effect.get("type")
        if effect_type == "variable_set":
            self.apply_variable_set(effect)
        elif effect_type == "variable_add":
            self.apply_variable_add(effect)

    def choose_current_option(self, option_index: int) -> None:
        if not self.current_choices:
            return
        option = self.current_choices[option_index]
        for effect in option.get("effects", []) or []:
            self.apply_choice_effect(effect)
        self.current_block_index += 1
        target_scene_id = option.get("gotoSceneId") or option.get("targetSceneId")
        self.current_choices = None
        if target_scene_id:
            self.set_scene(target_scene_id)
        self.advance_until_pause()
        self.auto_resume_write_enabled = True
        self.persist_auto_resume_snapshot()

    def advance_dialogue(self) -> None:
        if self.current_line:
            if not self.is_current_line_fully_visible():
                self.reveal_current_line_immediately()
                return
            self.current_line = None
            self.current_block_index += 1
            self.advance_until_pause()
            self.auto_resume_write_enabled = True
            self.persist_auto_resume_snapshot()

    def get_character_sprite_asset_id(self, character_id: str, expression_id: str | None) -> str | None:
        character = self.characters_by_id.get(character_id) or {}
        expressions = character.get("expressions", []) or []
        expression_map = {item.get("id"): item for item in expressions if item.get("id")}
        selected = expression_map.get(expression_id) or expression_map.get("expr_default")
        if selected and selected.get("spriteAssetId"):
            return selected["spriteAssetId"]
        return character.get("defaultSpriteId")

    def get_stage_zoom_scale(self) -> float:
        if not self.camera_zoom_effect:
            return 1.0
        action = str(self.camera_zoom_effect.get("action") or "zoom_in")
        strength = str(self.camera_zoom_effect.get("strength") or "medium")
        return CAMERA_ZOOM_SCALE.get((action, strength), 1.0)

    def get_stage_pan_offset(self) -> int:
        if not self.camera_pan_effect:
            return 0
        target = str(self.camera_pan_effect.get("target") or "center")
        strength = str(self.camera_pan_effect.get("strength") or "medium")
        base = CAMERA_PAN_OFFSET.get(target, 0.0)
        multiplier = CAMERA_PAN_STRENGTH_MULTIPLIER.get(strength, 1.0)
        return int(round(self.width * base * multiplier))

    def get_stage_shake_offset(self) -> tuple[int, int]:
        if not self.screen_shake_effect:
            return (0, 0)
        intensity = str(self.screen_shake_effect.get("intensity") or "medium")
        distance = SHAKE_DISTANCE.get(intensity, SHAKE_DISTANCE["medium"])
        phase = self.runtime_elapsed_seconds * 74.0
        return (int(math.sin(phase) * distance), int(math.cos(phase * 1.31) * distance * 0.55))

    def render_stage_surface(self, stage_surface) -> None:
        scale = self.get_stage_zoom_scale()
        offset_x = self.get_stage_pan_offset()
        shake_x, shake_y = self.get_stage_shake_offset()
        if abs(scale - 1.0) > 0.01:
            scaled_size = (max(1, int(self.width * scale)), max(1, int(self.height * scale)))
            stage_surface = self.pygame.transform.smoothscale(stage_surface, scaled_size)
        rect = stage_surface.get_rect(center=(self.width // 2 + offset_x + shake_x, self.height // 2 + shake_y))
        self.screen.blit(stage_surface, rect)

    def render_stage_effect_overlays(self) -> None:
        if self.screen_filter_effect:
            preset = str(self.screen_filter_effect.get("preset") or "memory")
            strength = str(self.screen_filter_effect.get("strength") or "medium")
            wash_color, base_alpha = SCREEN_FILTER_WASH.get(preset, SCREEN_FILTER_WASH["memory"])
            alpha = int(base_alpha * SCREEN_FILTER_STRENGTH_MULTIPLIER.get(strength, 1.0))
            wash = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            wash.fill((*wash_color, max(0, min(160, alpha))))
            self.screen.blit(wash, (0, 0))

        if self.depth_blur_effect:
            strength = str(self.depth_blur_effect.get("strength") or "medium")
            focus = str(self.depth_blur_effect.get("focus") or "full")
            alpha = DEPTH_BLUR_ALPHA.get(strength, DEPTH_BLUR_ALPHA["medium"])
            shade = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            if focus == "left":
                shade.fill((0, 0, 0, 0))
                self.pygame.draw.rect(shade, (0, 0, 0, alpha), self.pygame.Rect(int(self.width * 0.42), 0, int(self.width * 0.58), self.height))
            elif focus == "right":
                shade.fill((0, 0, 0, 0))
                self.pygame.draw.rect(shade, (0, 0, 0, alpha), self.pygame.Rect(0, 0, int(self.width * 0.58), self.height))
            elif focus == "center":
                shade.fill((0, 0, 0, 0))
                self.pygame.draw.rect(shade, (0, 0, 0, alpha), self.pygame.Rect(0, 0, int(self.width * 0.26), self.height))
                self.pygame.draw.rect(shade, (0, 0, 0, alpha), self.pygame.Rect(int(self.width * 0.74), 0, int(self.width * 0.26), self.height))
            else:
                shade.fill((0, 0, 0, alpha))
            self.screen.blit(shade, (0, 0))

    def render_screen_effect_overlays(self) -> None:
        if self.screen_fade_effect:
            color = FADE_COLORS.get(str(self.screen_fade_effect.get("color") or "black"), FADE_COLORS["black"])
            fade_surface = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            fade_surface.fill((*color, 220))
            self.screen.blit(fade_surface, (0, 0))

        if self.screen_flash_effect:
            color = FLASH_COLORS.get(str(self.screen_flash_effect.get("color") or "white"), FLASH_COLORS["white"])
            intensity = str(self.screen_flash_effect.get("intensity") or "medium")
            remaining = float(self.screen_flash_effect.get("remaining") or 0.0)
            duration = max(0.001, float(self.screen_flash_effect.get("durationSeconds") or 0.72))
            alpha = int(FLASH_ALPHA.get(intensity, FLASH_ALPHA["medium"]) * clamp(remaining / duration, 0.0, 1.0))
            flash_surface = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            flash_surface.fill((*color, max(0, min(255, alpha))))
            self.screen.blit(flash_surface, (0, 0))

    def render(self) -> None:
        pygame = self.pygame
        self.screen.fill(self.get_active_palette()["bgBottom"])
        stage_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.render_background(stage_surface)
        self.render_characters(stage_surface)
        self.render_particle_effect(stage_surface)
        self.render_stage_surface(stage_surface)
        self.render_stage_effect_overlays()
        self.render_status_bar()
        if self.current_choices:
            self.render_choices()
        elif self.current_line and self.current_line.get("type") == "video_play":
            self.render_video_card()
        elif self.current_line:
            self.render_dialogue()
        elif self.finished:
            self.render_finished()
        self.render_screen_effect_overlays()
        self.render_overlay()
        pygame.display.flip()

    def render_background(self, target=None) -> None:
        target = target or self.screen
        palette = self.get_active_palette()
        background = self._load_image(self.stage_background_asset_id)
        if background:
            bg_width, bg_height = background.get_size()
            scale = max(self.width / bg_width, self.height / bg_height)
            scaled = self.pygame.transform.smoothscale(
                background,
                (max(1, int(bg_width * scale)), max(1, int(bg_height * scale))),
            )
            rect = scaled.get_rect(center=(self.width // 2, self.height // 2))
            target.blit(scaled, rect)
        else:
            top = self.pygame.Surface((self.width, self.height // 2))
            bottom = self.pygame.Surface((self.width, self.height - self.height // 2))
            top.fill(palette["bgTop"])
            bottom.fill(palette["bgBottom"])
            target.blit(top, (0, 0))
            target.blit(bottom, (0, self.height // 2))
            label = "背景未加载" if self.stage_background_asset_id else "当前场景没有背景"
            self.blit_text_center(self.font_title, label, self.width // 2, self.height // 2 - 20, palette["muted"], target=target)

    def render_characters(self, target=None) -> None:
        target = target or self.screen
        palette = self.get_active_palette()
        position_x = {
            "left": int(self.width * 0.24),
            "center": int(self.width * 0.50),
            "right": int(self.width * 0.76),
        }
        for character_id, state in sorted(self.visible_characters.items(), key=lambda item: position_x.get(item[1].get("position") or "center", 0)):
            sprite_asset_id = self.get_character_sprite_asset_id(character_id, state.get("expressionId"))
            sprite = self._load_image(sprite_asset_id)
            x = position_x.get(state.get("position") or "center", self.width // 2)
            if sprite:
                sprite_width, sprite_height = sprite.get_size()
                max_height = int(self.height * 0.74)
                scale = min(max_height / max(sprite_height, 1), 1.6)
                scaled = self.pygame.transform.smoothscale(
                    sprite,
                    (max(1, int(sprite_width * scale)), max(1, int(sprite_height * scale))),
                )
                rect = scaled.get_rect(midbottom=(x, int(self.height * 0.88)))
                target.blit(scaled, rect)
            else:
                placeholder_rect = self.pygame.Rect(0, 0, 220, 420)
                placeholder_rect.midbottom = (x, int(self.height * 0.88))
                self.pygame.draw.rect(target, palette["placeholder"], placeholder_rect, border_radius=28)
                self.pygame.draw.rect(target, palette["panelBorder"], placeholder_rect, 2, border_radius=28)
                character_name = (self.characters_by_id.get(character_id) or {}).get("displayName") or character_id
                self.blit_text_center(self.font_body, character_name, placeholder_rect.centerx, placeholder_rect.centery - 16, palette["text"], target=target)
                self.blit_text_center(self.font_ui, "立绘未加载", placeholder_rect.centerx, placeholder_rect.centery + 24, palette["muted"], target=target)

    def render_status_bar(self) -> None:
        palette = self.get_active_palette()
        panel = self.pygame.Rect(20, 18, self.width - 40, 64)
        self.pygame.draw.rect(self.screen, (*palette["panel"], palette["panelAlpha"]), panel, border_radius=18)
        self.pygame.draw.rect(self.screen, palette["panelBorder"], panel, 1, border_radius=18)
        self.draw_game_ui_panel_frame(panel)
        project_title = self.project.get("title") or "Tony Na Engine"
        target_label = self.build_info.get("exportTargetLabel") or "原生 Runtime"
        status_text = f"{project_title} · {target_label}"
        self.screen.blit(self.font_ui.render(status_text, True, palette["text"]), (36, 30))
        self.screen.blit(self.font_ui.render(self.status_message, True, palette["muted"]), (36, 52))
        controls = (
            "↑↓：选择 · Enter：确认 · F11：全屏 · Esc：退出"
            if self.overlay_mode == "title"
            else "F1：系统 · F6：正式存档 · F7：读档 · F5：快存 · F8：快读 · F11：全屏 · Esc：关闭/退出"
        )
        control_surface = self.font_ui.render(controls, True, palette["muted"])
        self.screen.blit(control_surface, (self.width - control_surface.get_width() - 36, 30))

    def render_dialogue(self) -> None:
        line = self.current_line or {}
        panel = self.get_dialog_panel_rect(176)
        self.draw_dialog_panel(panel)
        padding_x = int(self.dialog_box_config.get("paddingX", 18))
        padding_y = int(self.dialog_box_config.get("paddingY", 14))
        text_left = panel.left + padding_x
        text_width = panel.width - padding_x * 2

        speaker_id = line.get("speakerId")
        speaker_name = ""
        if line.get("type") == "dialogue":
            character = self.characters_by_id.get(speaker_id) or {}
            speaker_name = character.get("displayName") or str(speaker_id or "")
        elif line.get("speakerName"):
            speaker_name = str(line.get("speakerName") or "")
        elif line.get("blockLabel"):
            speaker_name = str(line.get("blockLabel") or "")
        else:
            speaker_name = "旁白"

        current_top = panel.top + padding_y
        if speaker_name:
            speaker_surface = self.font_title.render(speaker_name, True, self.dialog_box_config.get("speakerColor", COLOR_TEXT))
            self.screen.blit(speaker_surface, (text_left, current_top))
            current_top += speaker_surface.get_height() + 12

        text = self.get_current_line_render_text()
        meta_surface = self.font_ui.render(self.build_save_summary_line(), True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED))
        meta_top = panel.bottom - padding_y - meta_surface.get_height()
        max_text_height = max(36, meta_top - current_top - 10)
        line_height = self.font_body.get_height() + 8
        max_lines = max(1, max_text_height // line_height)
        lines = wrap_text(self.font_body, text, text_width)
        for index, text_line in enumerate(lines[:max_lines]):
            self.screen.blit(
                self.font_body.render(text_line, True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
                (text_left, current_top + index * line_height),
            )

        self.screen.blit(meta_surface, (text_left, meta_top))

    def render_video_card(self) -> None:
        line = self.current_line or {}
        palette = self.get_active_palette()
        panel = self.pygame.Rect(0, 0, min(self.width - 88, 1040), min(self.height - 118, 610))
        panel.center = (self.width // 2, self.height // 2 + 18)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 244), panel, border_radius=30)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 76), panel, 2, border_radius=30)
        self.draw_game_ui_panel_frame(panel, "system")

        kicker = self.font_ui.render("NATIVE VIDEO BRIDGE", True, palette["accent"])
        self.screen.blit(kicker, (panel.left + 30, panel.top + 24))
        title = str(line.get("videoTitle") or "视频播放")
        self.screen.blit(self.font_title.render(title[:34], True, palette["text"]), (panel.left + 30, panel.top + 52))

        preview_result = self.get_video_preview_frame_result(line)
        preview_frame = preview_result.get("surface")
        preview_status = str(preview_result.get("status") or "")
        status_labels = [
            "已唤起播放器" if line.get("videoOpened") else "等待播放",
            "不可跳过" if line.get("videoSkippable") is False else "可跳过",
            "帧预览可用" if preview_frame else "桥接卡预览",
        ]
        pill_right = panel.right - 30
        for label in reversed(status_labels):
            label_surface = self.font_ui.render(label, True, palette["text"])
            pill_width = label_surface.get_width() + 22
            pill_rect = self.pygame.Rect(pill_right - pill_width, panel.top + 28, pill_width, 28)
            fill_color = palette["accent"] if label == "已唤起播放器" else palette["panel"]
            self.pygame.draw.rect(self.screen, with_alpha(fill_color, 62), pill_rect, border_radius=14)
            self.pygame.draw.rect(self.screen, with_alpha(palette["accentAlt"], 42), pill_rect, 1, border_radius=14)
            self.screen.blit(label_surface, (pill_rect.left + 11, pill_rect.top + 5))
            pill_right = pill_rect.left - 8

        preview_rect = self.pygame.Rect(panel.left + 30, panel.top + 96, panel.width - 60, max(170, panel.height - 274))
        self.pygame.draw.rect(self.screen, (5, 8, 16), preview_rect, border_radius=24)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 36), preview_rect, 1, border_radius=24)
        self.draw_game_ui_panel_frame(preview_rect)

        if preview_frame:
            image_width, image_height = preview_frame.get_size()
            image_area = preview_rect.inflate(-6, -6)
            fit_mode = str(line.get("videoFit") or "contain")
            if fit_mode == "cover":
                scale = max(image_area.width / max(1, image_width), image_area.height / max(1, image_height))
            else:
                scale = min(image_area.width / max(1, image_width), image_area.height / max(1, image_height))
            scaled = self.pygame.transform.smoothscale(
                preview_frame,
                (max(1, int(image_width * scale)), max(1, int(image_height * scale))),
            )
            previous_clip = self.screen.get_clip()
            self.screen.set_clip(preview_rect)
            self.screen.blit(scaled, scaled.get_rect(center=preview_rect.center))
            self.screen.set_clip(previous_clip)
            overlay = self.pygame.Surface((preview_rect.width, preview_rect.height), self.pygame.SRCALPHA)
            overlay.fill((5, 8, 16, 72))
            self.screen.blit(overlay, preview_rect.topleft)
        else:
            glow_surface = self.pygame.Surface((preview_rect.width, preview_rect.height), self.pygame.SRCALPHA)
            self.pygame.draw.circle(
                glow_surface,
                with_alpha(palette["accent"], 24),
                (int(preview_rect.width * 0.28), int(preview_rect.height * 0.35)),
                max(80, preview_rect.height // 2),
            )
            self.pygame.draw.circle(
                glow_surface,
                with_alpha(palette["accentAlt"], 20),
                (int(preview_rect.width * 0.78), int(preview_rect.height * 0.18)),
                max(70, preview_rect.height // 3),
            )
            self.screen.blit(glow_surface, preview_rect.topleft)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 42), preview_rect, 1, border_radius=24)
        self.draw_game_ui_panel_frame(preview_rect)

        play_radius = max(34, min(62, preview_rect.height // 5))
        self.pygame.draw.circle(self.screen, with_alpha(palette["accent"], 58), preview_rect.center, play_radius)
        self.pygame.draw.circle(self.screen, with_alpha(palette["accentAlt"], 82), preview_rect.center, play_radius, 2)
        triangle_size = play_radius * 0.72
        triangle = [
            (int(preview_rect.centerx - triangle_size * 0.28), int(preview_rect.centery - triangle_size * 0.48)),
            (int(preview_rect.centerx - triangle_size * 0.28), int(preview_rect.centery + triangle_size * 0.48)),
            (int(preview_rect.centerx + triangle_size * 0.52), preview_rect.centery),
        ]
        self.pygame.draw.polygon(self.screen, palette["text"], triangle)

        file_label = str(line.get("videoFileName") or "视频文件未找到")
        bridge_hint = "按 V 唤起系统播放器；播放结束后回到这个窗口继续。"
        if preview_frame:
            bridge_hint = "已读取视频画面帧；按 V 使用系统播放器完整播放。"
        elif preview_status:
            bridge_hint = f"{preview_status}；按 V 唤起系统播放器。"
        if not line.get("videoAssetPath"):
            bridge_hint = "视频文件缺失。可以继续剧情，但正式发布前需要重新导出素材。"
        self.blit_text_center(self.font_body, file_label[:42], preview_rect.centerx, preview_rect.bottom - 72, palette["text"])
        self.blit_text_center(self.font_ui, bridge_hint[:58], preview_rect.centerx, preview_rect.bottom - 40, palette["muted"])

        meta_top = preview_rect.bottom + 18
        clip_label = str(line.get("videoClipLabel") or "整段播放")
        meta_rows = [
            ("剪辑范围", clip_label),
            ("画面适配", str(line.get("videoFit") or "contain")),
            ("音量", f"{int(line.get('videoVolume') or 100)}%"),
        ]
        meta_left = panel.left + 34
        meta_width = max(130, (panel.width - 68) // len(meta_rows))
        for index, (label, value) in enumerate(meta_rows):
            row_rect = self.pygame.Rect(meta_left + index * meta_width, meta_top, meta_width - 12, 42)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 42), row_rect, border_radius=14)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 20), row_rect, 1, border_radius=14)
            self.screen.blit(self.font_ui.render(label, True, palette["muted"]), (row_rect.left + 12, row_rect.top + 6))
            value_surface = self.font_ui.render(value, True, palette["text"])
            self.screen.blit(value_surface, (row_rect.right - value_surface.get_width() - 12, row_rect.top + 22))

        timeline_rect = self.pygame.Rect(panel.left + 34, meta_top + 56, panel.width - 68, 8)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 26), timeline_rect, border_radius=4)
        start_time = float(line.get("videoStartTimeSeconds") or 0)
        end_time = float(line.get("videoEndTimeSeconds") or 0)
        if start_time > 0 or end_time > 0:
            virtual_duration = max(end_time, start_time + 12, 30)
            start_x = timeline_rect.left + int(timeline_rect.width * min(start_time / virtual_duration, 1))
            end_ratio = min((end_time or virtual_duration) / virtual_duration, 1)
            end_x = timeline_rect.left + int(timeline_rect.width * end_ratio)
            selected_rect = self.pygame.Rect(start_x, timeline_rect.top, max(8, end_x - start_x), timeline_rect.height)
            self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 82), selected_rect, border_radius=4)
        else:
            self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 58), timeline_rect, border_radius=4)

        self.video_hotspots = []
        button_y = panel.bottom - 54
        buttons = [
            ("play-video", "V 播放/重新打开", panel.left + 34, 168, False),
            (
                "continue-video",
                "Enter 继续",
                panel.right - 154,
                120,
                line.get("videoSkippable") is False and bool(line.get("videoAssetPath")) and not bool(line.get("videoOpened")),
            ),
        ]
        for action, label, left, width, disabled in buttons:
            button_rect = self.pygame.Rect(left, button_y, width, 36)
            active = action == "play-video" and not disabled
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if active else palette["panel"], 72 if active else 48),
                button_rect,
                border_radius=15,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if active else palette["panelBorder"], 80 if active else 32),
                button_rect,
                1,
                border_radius=15,
            )
            self.draw_game_ui_button_frame(
                button_rect,
                self.get_game_ui_button_state(button_rect, active=active, disabled=disabled),
            )
            self.blit_text_center(self.font_ui, label, button_rect.centerx, button_rect.top + 9, palette["muted"] if disabled else palette["text"])
            self.video_hotspots.append({"kind": action, "rect": button_rect, "disabled": disabled})

        hint = "不可跳过视频需要先播放一次，再确认继续。" if buttons[1][4] else "也可以按 Space / Enter 继续。"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 34, panel.bottom - 86))

    def render_choices(self) -> None:
        option_count = len(self.current_choices or [])
        panel = self.get_dialog_panel_rect(max(212, 86 + option_count * 54))
        self.draw_dialog_panel(panel)
        padding_x = int(self.dialog_box_config.get("paddingX", 18))
        padding_y = int(self.dialog_box_config.get("paddingY", 14))
        title = self.font_title.render("请选择下一步", True, self.dialog_box_config.get("speakerColor", COLOR_TEXT))
        self.screen.blit(title, (panel.left + padding_x, panel.top + padding_y))
        button_top = panel.top + padding_y + title.get_height() + 18
        button_left = panel.left + padding_x
        button_width = panel.width - padding_x * 2
        active_fill = with_alpha(self.dialog_box_config.get("borderColor", COLOR_ACCENT), 88)
        idle_fill = with_alpha(self.dialog_box_config.get("backgroundColor", COLOR_PANEL), max(28, self.dialog_box_config.get("backgroundOpacity", 0)))
        border_color = with_alpha(self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), max(24, self.dialog_box_config.get("borderOpacity", 0)))

        for index, option in enumerate(self.current_choices or []):
            row_rect = self.pygame.Rect(button_left, button_top + index * 52, button_width, 40)
            is_active = index == self.current_choice_index
            fill = active_fill if is_active else idle_fill
            border = with_alpha(self.dialog_box_config.get("speakerColor", COLOR_ACCENT_ALT), 88) if is_active else border_color
            self.pygame.draw.rect(self.screen, fill, row_rect, border_radius=16)
            self.pygame.draw.rect(self.screen, border, row_rect, 2, border_radius=16)
            self.draw_game_ui_button_frame(row_rect, self.get_game_ui_button_state(row_rect, active=is_active))
            label = str(option.get("text") or f"选项 {index + 1}")
            self.screen.blit(
                self.font_body.render(label, True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
                (row_rect.left + 18, row_rect.top + 5),
            )

    def render_finished(self) -> None:
        panel = self.get_dialog_panel_rect(220)
        panel.centery = self.height // 2
        self.draw_dialog_panel(panel)
        self.blit_text_center(self.font_title, "本条路线已经结束", panel.centerx, panel.top + 48, self.dialog_box_config.get("speakerColor", COLOR_TEXT))
        self.blit_text_center(self.font_body, self.finished_message or "剧情结束。", panel.centerx, panel.top + 104, self.dialog_box_config.get("textColor", COLOR_TEXT_MUTED))
        self.blit_text_center(self.font_ui, "按 Esc 退出原生 Runtime", panel.centerx, panel.top + 158, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED))

    def render_overlay(self) -> None:
        if not self.overlay_mode:
            self.overlay_hotspots = []
            return
        palette = self.get_active_palette()
        backdrop = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
        backdrop.fill(palette["overlay"])
        self.screen.blit(backdrop, (0, 0))
        self.overlay_hotspots = []
        if self.overlay_mode == "title":
            self.render_title_overlay()
        elif self.overlay_mode in {"save", "load"}:
            self.render_save_dialog_overlay()
        elif self.overlay_mode == "system":
            self.render_system_menu_overlay()
        elif self.overlay_mode == "profile":
            self.render_profile_overlay()
        elif self.overlay_mode == "auto-resume":
            self.render_auto_resume_overlay()
        elif self.overlay_mode == "settings":
            self.render_settings_overlay()
        elif self.overlay_mode == "archives":
            self.render_archive_overlay()
        elif self.overlay_mode == "archive-detail":
            self.render_archive_detail_overlay()

    def render_title_overlay(self) -> None:
        palette = self.get_active_palette()
        menu_items = self.get_title_menu_items()
        panel = self.pygame.Rect(0, 0, min(self.width - 84, 1060), min(self.height - 92, 610))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 242), panel, border_radius=32)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 78), panel, 2, border_radius=32)
        self.draw_game_ui_panel_frame(panel, "system")

        glow = self.pygame.Surface((panel.width, panel.height), self.pygame.SRCALPHA)
        self.pygame.draw.circle(glow, with_alpha(palette["accent"], 34), (int(panel.width * 0.28), int(panel.height * 0.24)), 190)
        self.pygame.draw.circle(glow, with_alpha(palette["accentAlt"], 30), (int(panel.width * 0.88), int(panel.height * 0.14)), 170)
        self.screen.blit(glow, panel.topleft)

        logo_rect = self.pygame.Rect(panel.left + 46, panel.top + 70, 300, 250)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 68), logo_rect, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 36), logo_rect, 1, border_radius=28)
        self.draw_game_ui_panel_frame(logo_rect)
        logo = self.get_title_logo_image()
        if logo:
            logo_width, logo_height = logo.get_size()
            scale = min(logo_rect.width * 0.86 / max(1, logo_width), logo_rect.height * 0.86 / max(1, logo_height))
            scaled = self.pygame.transform.smoothscale(
                logo,
                (max(1, int(logo_width * scale)), max(1, int(logo_height * scale))),
            )
            self.screen.blit(scaled, scaled.get_rect(center=logo_rect.center))
        else:
            self.blit_text_center(self.font_title, "TNE", logo_rect.centerx, logo_rect.centery - 18, palette["text"])
            self.blit_text_center(self.font_ui, "Tony Na Engine", logo_rect.centerx, logo_rect.centery + 26, palette["muted"])

        title_left = logo_rect.right + 42
        title_top = panel.top + 78
        project_title = str(self.project.get("title") or self.project.get("name") or "Tony Na Engine")
        self.screen.blit(self.font_ui.render("NATIVE RUNTIME PREVIEW", True, palette["accent"]), (title_left, title_top))
        self.screen.blit(self.font_title.render(project_title[:28], True, palette["text"]), (title_left, title_top + 34))
        summary = f"{len(self.chapters)} 章 · {len(self.scenes_by_id)} 场景 · 正式存档 {self.formal_save_slot_count} 格"
        self.screen.blit(self.font_ui.render(summary, True, palette["muted"]), (title_left, title_top + 82))
        self.screen.blit(
            self.font_ui.render("标题页支持续玩、读档、设置和资料馆，适合作为独立 App 的第一屏。", True, palette["muted"]),
            (title_left, title_top + 112),
        )

        menu_left = title_left
        menu_top = title_top + 160
        menu_width = panel.right - menu_left - 46
        row_height = 56
        for index, item in enumerate(menu_items):
            row_rect = self.pygame.Rect(menu_left, menu_top + index * row_height, menu_width, 46)
            is_active = index == self.title_menu_index
            enabled = bool(item.get("enabled", True))
            fill_color = palette["accent"] if is_active else palette["panel"]
            fill_alpha = 78 if is_active else 36
            border_color = palette["accentAlt"] if is_active else palette["panelBorder"]
            self.pygame.draw.rect(self.screen, with_alpha(fill_color, fill_alpha if enabled else 20), row_rect, border_radius=18)
            self.pygame.draw.rect(self.screen, with_alpha(border_color, 86 if is_active else 24), row_rect, 1, border_radius=18)
            self.draw_game_ui_button_frame(
                row_rect,
                self.get_game_ui_button_state(row_rect, active=is_active, disabled=not enabled),
            )
            label_color = palette["text"] if enabled else palette["muted"]
            self.screen.blit(self.font_body.render(str(item["label"]), True, label_color), (row_rect.left + 18, row_rect.top + 6))
            subtitle = str(item.get("subtitle") or "")
            subtitle_surface = self.font_ui.render(subtitle[:46], True, palette["muted"])
            self.screen.blit(subtitle_surface, (row_rect.right - subtitle_surface.get_width() - 18, row_rect.top + 15))
            self.overlay_hotspots.append({"kind": "title-item", "value": item["key"], "rect": row_rect})

        footer = "↑↓ 选择 · Enter 确认 · F11 全屏 · Esc 退出"
        self.screen.blit(self.font_ui.render(footer, True, palette["muted"]), (panel.left + 46, panel.bottom - 48))

    def render_save_dialog_overlay(self) -> None:
        dialog_data = self.get_save_dialog_data()
        panel = self.pygame.Rect(0, 0, min(self.width - 88, 1040), min(self.height - 112, 620))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, with_alpha(self.dialog_box_config.get("backgroundColor", COLOR_PANEL), 96), panel, border_radius=28)
        self.pygame.draw.rect(
            self.screen,
            with_alpha(self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 72),
            panel,
            2,
            border_radius=28,
        )
        self.draw_game_ui_panel_frame(panel, "system")

        title = "正式存档" if self.overlay_mode == "save" else "读取存档"
        title_surface = self.font_title.render(title, True, self.dialog_box_config.get("speakerColor", COLOR_TEXT))
        subtitle = f"第 {dialog_data['page'] + 1} / {dialog_data['pageCount']} 页 · 共 {dialog_data['slotCount']} 格"
        subtitle_surface = self.font_ui.render(subtitle, True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED))
        self.screen.blit(title_surface, (panel.left + 28, panel.top + 24))
        self.screen.blit(subtitle_surface, (panel.left + 28, panel.top + 58))

        quick_save = dialog_data.get("quickSave") or {}
        quick_rect = self.pygame.Rect(panel.left + 28, panel.top + 92, panel.width - 56, 72)
        self.pygame.draw.rect(self.screen, with_alpha(self.dialog_box_config.get("backgroundColor", COLOR_PANEL), 42), quick_rect, border_radius=18)
        self.pygame.draw.rect(
            self.screen,
            with_alpha(self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 26),
            quick_rect,
            1,
            border_radius=18,
        )
        self.draw_game_ui_panel_frame(quick_rect, "save")
        quick_title = "快速存档" if not quick_save.get("isEmpty") else "快速存档（空）"
        self.screen.blit(
            self.font_ui.render(quick_title, True, self.dialog_box_config.get("speakerColor", COLOR_TEXT)),
            (quick_rect.left + 16, quick_rect.top + 10),
        )
        quick_meta = f"{quick_save.get('savedAt')} · {quick_save.get('sceneName') or '尚未创建'}"
        self.screen.blit(
            self.font_ui.render(quick_meta, True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED)),
            (quick_rect.left + 16, quick_rect.top + 34),
        )
        quick_summary = str(quick_save.get("summaryText") or "空")
        self.screen.blit(
            self.font_ui.render(quick_summary[:78], True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
            (quick_rect.left + 16, quick_rect.top + 52),
        )

        slots = dialog_data.get("visibleSlots") or []
        card_gap = 16
        card_width = (panel.width - 56 - card_gap) // 2
        card_height = 116
        cards_top = quick_rect.bottom + 22
        for visible_index, slot in enumerate(slots):
            row = visible_index // 2
            column = visible_index % 2
            card_rect = self.pygame.Rect(
                panel.left + 28 + column * (card_width + card_gap),
                cards_top + row * (card_height + 14),
                card_width,
                card_height,
            )
            is_active = visible_index == self.overlay_focus_index
            fill_opacity = 78 if is_active else 34
            border_opacity = 92 if is_active else 24
            self.pygame.draw.rect(
                self.screen,
                with_alpha(
                    self.dialog_box_config.get("borderColor", COLOR_ACCENT) if is_active else self.dialog_box_config.get("backgroundColor", COLOR_PANEL),
                    fill_opacity,
                ),
                card_rect,
                border_radius=22,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(
                    self.dialog_box_config.get("speakerColor", COLOR_ACCENT_ALT) if is_active else self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER),
                    border_opacity,
                ),
                card_rect,
                2,
                border_radius=22,
            )
            self.draw_game_ui_panel_frame(card_rect, "save")
            label = str(slot.get("label") or "")
            scene_name = str(slot.get("sceneName") or ("空位" if slot.get("isEmpty") else "未命名场景"))
            summary_text = str(slot.get("summaryText") or "")
            if slot.get("finished"):
                summary_text = "路线结束 · " + summary_text
            saved_at = str(slot.get("savedAt") or "尚未保存")
            self.screen.blit(
                self.font_ui.render(label, True, self.dialog_box_config.get("speakerColor", COLOR_TEXT)),
                (card_rect.left + 16, card_rect.top + 12),
            )
            self.screen.blit(
                self.font_body.render(scene_name[:22], True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
                (card_rect.left + 16, card_rect.top + 34),
            )
            self.screen.blit(
                self.font_ui.render(saved_at, True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED)),
                (card_rect.left + 16, card_rect.top + 72),
            )
            self.screen.blit(
                self.font_ui.render(summary_text[:40], True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
                (card_rect.left + 16, card_rect.top + 92),
            )
            self.overlay_hotspots.append({"kind": "slot", "value": visible_index, "rect": card_rect})

        button_y = panel.bottom - 58
        controls = [
            ("prev", "上一页", panel.left + 28),
            ("next", "下一页", panel.left + 168),
            ("switch", "切换存/读", panel.left + 308),
            ("close", "关闭", panel.right - 124),
        ]
        for action, label, left in controls:
            button_rect = self.pygame.Rect(left, button_y, 108 if action != "switch" else 132, 34)
            self.pygame.draw.rect(self.screen, with_alpha(self.dialog_box_config.get("backgroundColor", COLOR_PANEL), 58), button_rect, border_radius=14)
            self.pygame.draw.rect(
                self.screen,
                with_alpha(self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 42),
                button_rect,
                1,
                border_radius=14,
            )
            self.draw_game_ui_button_frame(button_rect, self.get_game_ui_button_state(button_rect))
            self.blit_text_center(
                self.font_ui,
                label,
                button_rect.centerx,
                button_rect.top + 8,
                self.dialog_box_config.get("textColor", COLOR_TEXT),
            )
            self.overlay_hotspots.append({"kind": action, "rect": button_rect})

        hint = "数字键 1-6 选槽位 · ←→ 切页 · Enter 执行 · Esc 关闭"
        self.screen.blit(
            self.font_ui.render(hint, True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED)),
            (panel.left + 28, panel.bottom - 88),
        )

    def get_profile_total_play_ms(self) -> int:
        profile = sanitize_player_profile(self.player_profile)
        total_ms = int(profile.get("totalPlayMs") or 0)
        if self.profile_session_started_at_ms:
            total_ms += max(0, self.pygame.time.get_ticks() - self.profile_session_started_at_ms)
        return total_ms

    def render_profile_overlay(self) -> None:
        palette = self.get_active_palette()
        profile = sanitize_player_profile(self.player_profile)
        panel = self.pygame.Rect(0, 0, min(self.width - 96, 700), min(self.height - 112, 500))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")
        self.screen.blit(self.font_title.render("玩家档案", True, palette["text"]), (panel.left + 30, panel.top + 26))
        self.screen.blit(
            self.font_ui.render("本地记录，不会上传；用于统计游玩和续玩入口。", True, palette["muted"]),
            (panel.left + 30, panel.top + 62),
        )

        rows = [
            ("累计游玩", format_play_duration(self.get_profile_total_play_ms())),
            ("启动次数", f"{int(profile.get('sessionCount') or 0)} 次"),
            ("续玩次数", f"{int(profile.get('resumedCount') or 0)} 次"),
            ("回到开头", f"{int(profile.get('returnToTitleCount') or 0)} 次"),
            ("首次游玩", format_snapshot_saved_at(profile.get("firstPlayedAt"))),
            ("最近启动", format_snapshot_saved_at(profile.get("lastPlayedAt"))),
            ("最近退出", format_snapshot_saved_at(profile.get("lastEndedAt"))),
        ]
        auto_resume_label = "无"
        if self.auto_resume_snapshot:
            auto_resume_label = f"{self.auto_resume_snapshot.get('sceneName') or '未命名场景'} · {format_snapshot_saved_at(self.auto_resume_snapshot.get('savedAt'))}"
        rows.append(("续玩记录", auto_resume_label))

        row_top = panel.top + 108
        for index, (label, value) in enumerate(rows):
            row_rect = self.pygame.Rect(panel.left + 30, row_top + index * 38, panel.width - 60, 30)
            if index % 2 == 0:
                self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 18), row_rect, border_radius=12)
            self.screen.blit(self.font_ui.render(label, True, palette["muted"]), (row_rect.left + 12, row_rect.top + 6))
            value_surface = self.font_ui.render(value, True, palette["text"])
            self.screen.blit(value_surface, (row_rect.right - value_surface.get_width() - 12, row_rect.top + 6))

        close_rect = self.pygame.Rect(panel.right - 138, panel.bottom - 58, 108, 34)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 58), close_rect, border_radius=14)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 42), close_rect, 1, border_radius=14)
        self.draw_game_ui_button_frame(close_rect, self.get_game_ui_button_state(close_rect))
        self.blit_text_center(self.font_ui, "关闭", close_rect.centerx, close_rect.top + 8, palette["text"])
        self.overlay_hotspots.append({"kind": "close", "rect": close_rect})
        self.screen.blit(self.font_ui.render("Enter / Esc 关闭", True, palette["muted"]), (panel.left + 30, panel.bottom - 48))

    def render_auto_resume_overlay(self) -> None:
        palette = self.get_active_palette()
        snapshot = self.auto_resume_snapshot or load_project_auto_resume(self.project_id)
        panel = self.pygame.Rect(0, 0, min(self.width - 96, 720), min(self.height - 112, 420))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")
        self.screen.blit(self.font_title.render("续玩记录", True, palette["text"]), (panel.left + 30, panel.top + 26))
        self.screen.blit(
            self.font_ui.render("每次停在台词、选项或结束页时，原生 Runtime 会自动更新这里。", True, palette["muted"]),
            (panel.left + 30, panel.top + 62),
        )

        card_rect = self.pygame.Rect(panel.left + 30, panel.top + 108, panel.width - 60, 150)
        self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 26), card_rect, border_radius=20)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 36), card_rect, 1, border_radius=20)
        self.draw_game_ui_panel_frame(card_rect, "save")
        if snapshot:
            scene_name = str(snapshot.get("sceneName") or snapshot.get("sceneId") or "未命名场景")
            summary = str(snapshot.get("summaryText") or snapshot.get("finishedMessage") or "当前没有摘要。")
            meta = f"{format_snapshot_saved_at(snapshot.get('savedAt'))} · 第 {int(snapshot.get('blockIndex') or 0) + 1} 张卡"
            if snapshot.get("finished"):
                meta += " · 已结束"
            self.screen.blit(self.font_body.render(scene_name[:28], True, palette["text"]), (card_rect.left + 18, card_rect.top + 20))
            self.screen.blit(self.font_ui.render(meta, True, palette["muted"]), (card_rect.left + 18, card_rect.top + 58))
            self.screen.blit(self.font_ui.render(summary[:72], True, palette["text"]), (card_rect.left + 18, card_rect.top + 94))
        else:
            self.blit_text_center(self.font_body, "当前没有续玩记录", card_rect.centerx, card_rect.top + 42, palette["muted"])
            self.blit_text_center(self.font_ui, "推进一次剧情或读入存档后会自动生成。", card_rect.centerx, card_rect.top + 88, palette["muted"])

        controls = []
        if snapshot:
            controls.extend([("auto-resume-load", "读取续玩"), ("auto-resume-clear", "清除记录")])
        controls.append(("close", "关闭"))
        button_width = 118
        gap = 14
        start_left = panel.right - 30 - len(controls) * button_width - (len(controls) - 1) * gap
        button_y = panel.bottom - 62
        for index, (kind, label) in enumerate(controls):
            button_rect = self.pygame.Rect(start_left + index * (button_width + gap), button_y, button_width, 36)
            is_primary = kind == "auto-resume-load"
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if is_primary else palette["panel"], 72 if is_primary else 58),
                button_rect,
                border_radius=14,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if is_primary else palette["panelBorder"], 84 if is_primary else 42),
                button_rect,
                1,
                border_radius=14,
            )
            self.draw_game_ui_button_frame(button_rect, self.get_game_ui_button_state(button_rect, active=is_primary))
            self.blit_text_center(self.font_ui, label, button_rect.centerx, button_rect.top + 9, palette["text"])
            self.overlay_hotspots.append({"kind": kind, "rect": button_rect})

        hint = "Enter 读取续玩 · C 清除记录 · Esc 关闭" if snapshot else "Esc 关闭"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 30, panel.bottom - 50))

    def render_system_menu_overlay(self) -> None:
        palette = self.get_active_palette()
        panel_height = min(self.height - 72, max(508, 154 + len(SYSTEM_MENU_ITEMS) * 44))
        panel = self.pygame.Rect(0, 0, 420, panel_height)
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 244), panel, border_radius=28)
        self.pygame.draw.rect(
            self.screen,
            with_alpha(palette["panelBorder"], 72),
            panel,
            2,
            border_radius=28,
        )
        self.draw_game_ui_panel_frame(panel, "system")
        title_surface = self.font_title.render("系统菜单", True, palette["text"])
        self.screen.blit(title_surface, (panel.left + 26, panel.top + 24))
        self.screen.blit(
            self.font_ui.render("原生 Runtime 控制台", True, palette["muted"]),
            (panel.left + 26, panel.top + 58),
        )

        button_top = panel.top + 96
        for index, (item_key, item_label) in enumerate(SYSTEM_MENU_ITEMS):
            row_rect = self.pygame.Rect(panel.left + 26, button_top + index * 44, panel.width - 52, 36)
            is_active = index == self.system_menu_index
            self.pygame.draw.rect(
                self.screen,
                with_alpha(
                    palette["accent"] if is_active else palette["panel"],
                    72 if is_active else 36,
                ),
                row_rect,
                border_radius=16,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(
                    palette["accentAlt"] if is_active else palette["panelBorder"],
                    84 if is_active else 22,
                ),
                row_rect,
                1,
                border_radius=16,
            )
            self.draw_game_ui_button_frame(row_rect, self.get_game_ui_button_state(row_rect, active=is_active))
            self.screen.blit(
                self.font_body.render(item_label, True, palette["text"]),
                (row_rect.left + 16, row_rect.top + 4),
            )
            self.overlay_hotspots.append({"kind": "system-item", "value": item_key, "rect": row_rect})

        hint = "↑↓ 切换 · Enter 执行 · Esc 关闭"
        self.screen.blit(
            self.font_ui.render(hint, True, palette["muted"]),
            (panel.left + 26, panel.bottom - 44),
        )

    def render_settings_overlay(self) -> None:
        palette = self.get_active_palette()
        panel = self.pygame.Rect(0, 0, 560, 486)
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(
            self.screen,
            with_alpha(palette["panelBorder"], 72),
            panel,
            2,
            border_radius=28,
        )
        self.draw_game_ui_panel_frame(panel, "system")
        self.screen.blit(self.font_title.render("体验设置", True, palette["text"]), (panel.left + 28, panel.top + 24))
        self.screen.blit(
            self.font_ui.render("主题 / 显示模式 / 文字速度 / 四路音量", True, palette["muted"]),
            (panel.left + 28, panel.top + 58),
        )

        button_top = panel.top + 96
        row_height = 44
        for index, (setting_key, setting_label) in enumerate(SETTINGS_MENU_ITEMS):
            row_rect = self.pygame.Rect(panel.left + 24, button_top + index * row_height, panel.width - 48, 36)
            is_active = index == self.settings_menu_index
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if is_active else palette["panel"], 70 if is_active else 34),
                row_rect,
                border_radius=16,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if is_active else palette["panelBorder"], 82 if is_active else 22),
                row_rect,
                1,
                border_radius=16,
            )
            self.draw_game_ui_button_frame(row_rect, self.get_game_ui_button_state(row_rect, active=is_active))
            self.screen.blit(self.font_ui.render(setting_label, True, palette["text"]), (row_rect.left + 14, row_rect.top + 10))
            value_label = self.get_setting_value_label(setting_key)
            value_surface = self.font_ui.render(value_label, True, palette["muted"])
            self.screen.blit(value_surface, (row_rect.right - value_surface.get_width() - 48, row_rect.top + 10))
            self.screen.blit(self.font_ui.render("◀", True, palette["text"]), (row_rect.right - 32, row_rect.top + 9))
            self.screen.blit(self.font_ui.render("▶", True, palette["text"]), (row_rect.right - 16, row_rect.top + 9))
            self.overlay_hotspots.append({"kind": "settings-item", "value": setting_key, "rect": row_rect})

        hint = "↑↓ 切换 · ←→ 调整 · Enter 切换 · Esc 返回"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 44))

    def render_archive_overlay(self) -> None:
        palette = self.get_active_palette()
        entries = self.get_archive_entries(self.current_archive_key)
        selected_entry = self.get_selected_archive_entry()
        visible_start, visible_entries = self.get_visible_archive_window(entries)
        panel = self.pygame.Rect(0, 0, min(self.width - 72, 1120), min(self.height - 92, 660))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")
        title = ARCHIVE_MENU_ITEMS.get(self.current_archive_key, "资料馆")
        self.screen.blit(self.font_title.render("资料馆", True, palette["text"]), (panel.left + 26, panel.top + 24))
        unlocked_count = sum(1 for entry in entries if entry.get("unlocked"))
        completion_suffix = ""
        if self.current_archive_key == "endings":
            completion_suffix = f" · 累计通关 {int(self.archive_progress.get('endingCompletionCount') or 0)} 次"
        summary = f"{title} · 已解锁 {unlocked_count} / {len(entries)}{completion_suffix}"
        self.screen.blit(self.font_ui.render(summary, True, palette["muted"]), (panel.left + 26, panel.top + 58))

        tabs_top = panel.top + 92
        tab_left = panel.left + 24
        tab_gap = 10
        tab_count = max(1, len(ARCHIVE_MENU_SEQUENCE))
        available_tab_width = panel.width - 48 - tab_gap * (tab_count - 1)
        tab_width = max(88, available_tab_width // tab_count)
        tab_height = 34
        for index, archive_key in enumerate(ARCHIVE_MENU_SEQUENCE):
            tab_rect = self.pygame.Rect(tab_left + index * (tab_width + tab_gap), tabs_top, tab_width, tab_height)
            is_active = archive_key == self.current_archive_key
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if is_active else palette["panel"], 74 if is_active else 34),
                tab_rect,
                border_radius=16,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if is_active else palette["panelBorder"], 84 if is_active else 20),
                tab_rect,
                1,
                border_radius=16,
            )
            self.draw_game_ui_button_frame(tab_rect, self.get_game_ui_button_state(tab_rect, active=is_active))
            self.blit_text_center(self.font_ui, ARCHIVE_MENU_ITEMS[archive_key], tab_rect.centerx, tab_rect.top + 8, palette["text"])
            self.overlay_hotspots.append({"kind": "archive-tab", "value": archive_key, "rect": tab_rect})

        list_rect = self.pygame.Rect(panel.left + 24, panel.top + 138, 360, panel.height - 190)
        hero_rect = self.pygame.Rect(list_rect.right + 20, panel.top + 138, panel.right - list_rect.right - 44, panel.height - 190)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 42), list_rect, border_radius=20)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 24), list_rect, 1, border_radius=20)
        self.draw_game_ui_panel_frame(list_rect)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 42), hero_rect, border_radius=20)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 24), hero_rect, 1, border_radius=20)
        self.draw_game_ui_panel_frame(hero_rect)

        row_top = list_rect.top + 14
        row_height = 54
        for row_index, (entry_index, entry) in enumerate(visible_entries):
            row_rect = self.pygame.Rect(list_rect.left + 12, row_top + row_index * row_height, list_rect.width - 24, 44)
            is_active = entry_index == self.archive_selection_index
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if is_active else palette["panel"], 68 if is_active else 26),
                row_rect,
                border_radius=16,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if is_active else palette["panelBorder"], 82 if is_active else 20),
                row_rect,
                1,
                border_radius=16,
            )
            self.draw_game_ui_button_frame(row_rect, self.get_game_ui_button_state(row_rect, active=is_active))
            title_text = entry["name"] if entry.get("unlocked") else "未解锁"
            self.screen.blit(self.font_ui.render(title_text[:22], True, palette["text"]), (row_rect.left + 14, row_rect.top + 8))
            subtitle = entry.get("subtitle") or ""
            if not entry.get("unlocked"):
                subtitle = "推进剧情后解锁"
            self.screen.blit(self.font_ui.render(subtitle[:28], True, palette["muted"]), (row_rect.left + 14, row_rect.top + 24))
            self.overlay_hotspots.append({"kind": "archive-item", "value": entry_index, "rect": row_rect})

        if len(entries) > len(visible_entries):
            scroll_label = f"显示 {visible_start + 1}-{visible_start + len(visible_entries)} / {len(entries)}"
            self.screen.blit(self.font_ui.render(scroll_label, True, palette["muted"]), (list_rect.left + 14, list_rect.bottom - 26))

        if not selected_entry:
            self.blit_text_center(self.font_title, "当前没有可显示条目", hero_rect.centerx, hero_rect.top + 90, palette["muted"])
        else:
            hero_title = selected_entry["name"] if selected_entry.get("unlocked") else "？？？"
            self.screen.blit(self.font_title.render(hero_title, True, palette["text"]), (hero_rect.left + 22, hero_rect.top + 22))
            self.screen.blit(
                self.font_ui.render(
                    selected_entry.get("subtitle") if selected_entry.get("unlocked") else "推进剧情后解锁",
                    True,
                    palette["muted"],
                ),
                (hero_rect.left + 22, hero_rect.top + 62),
            )
            preview_rect = self.pygame.Rect(hero_rect.left + 22, hero_rect.top + 96, hero_rect.width - 44, hero_rect.height - 190)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 22), preview_rect, border_radius=18)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 16), preview_rect, 1, border_radius=18)
            self.draw_game_ui_panel_frame(preview_rect)

            preview_asset_id = str(selected_entry.get("previewAssetId") or "")
            if self.current_archive_key == "gallery" and selected_entry.get("unlocked"):
                image = self._load_image(str(selected_entry.get("id") or ""))
                if image:
                    image_width, image_height = image.get_size()
                    scale = min(preview_rect.width / max(1, image_width), preview_rect.height / max(1, image_height))
                    scaled = self.pygame.transform.smoothscale(
                        image,
                        (max(1, int(image_width * scale)), max(1, int(image_height * scale))),
                    )
                    image_rect = scaled.get_rect(center=preview_rect.center)
                    self.screen.blit(scaled, image_rect)
                else:
                    self.blit_text_center(self.font_body, "CG 预览未加载", preview_rect.centerx, preview_rect.centery - 16, palette["muted"])
            elif self.current_archive_key in {"chapters", "locations", "characters", "endings"} and selected_entry.get("unlocked") and preview_asset_id:
                image = self._load_image(preview_asset_id)
                if image:
                    image_width, image_height = image.get_size()
                    scale = min(preview_rect.width / max(1, image_width), preview_rect.height / max(1, image_height))
                    scaled = self.pygame.transform.smoothscale(
                        image,
                        (max(1, int(image_width * scale)), max(1, int(image_height * scale))),
                    )
                    image_rect = scaled.get_rect(center=preview_rect.center)
                    self.screen.blit(scaled, image_rect)
                else:
                    self.blit_text_center(self.font_body, "预览图未加载", preview_rect.centerx, preview_rect.centery - 16, palette["muted"])
            else:
                preview_label = {
                    "chapters": "章节回放预览",
                    "music": "音乐鉴赏预览",
                    "gallery": "CG 回想预览",
                    "locations": "地点图鉴预览",
                    "characters": "角色图鉴预览",
                    "narrations": "旁白摘录预览",
                    "relations": "关系图鉴预览",
                    "voices": "语音回听预览",
                    "endings": "结局回放预览",
                    "achievements": "成就馆预览",
                }.get(self.current_archive_key, "资料馆预览")
                self.blit_text_center(self.font_body, preview_label, preview_rect.centerx, preview_rect.centery - 16, palette["muted"])

            notes = selected_entry.get("notes") or ""
            preview_copy = str(selected_entry.get("previewText") or "")
            speaker_copy = str(selected_entry.get("previewSpeakerName") or "")
            if speaker_copy:
                self.screen.blit(
                    self.font_ui.render(speaker_copy[:28], True, palette["text"]),
                    (hero_rect.left + 22, hero_rect.bottom - 102),
                )
            self.screen.blit(
                self.font_ui.render(
                    (preview_copy if selected_entry.get("unlocked") and preview_copy else notes if selected_entry.get("unlocked") else "推进剧情后，这个条目会自动亮起。")[:72],
                    True,
                    palette["muted"],
                ),
                (hero_rect.left + 22, hero_rect.bottom - 78),
            )
            action_label = selected_entry.get("actionLabel") if selected_entry.get("unlocked") else "未解锁"
            action_rect = self.pygame.Rect(hero_rect.left + 22, hero_rect.bottom - 52, 160, 32)
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if selected_entry.get("actionEnabled") else palette["panel"], 76 if selected_entry.get("actionEnabled") else 24),
                action_rect,
                border_radius=14,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if selected_entry.get("actionEnabled") else palette["panelBorder"], 84 if selected_entry.get("actionEnabled") else 20),
                action_rect,
                1,
                border_radius=14,
            )
            self.draw_game_ui_button_frame(
                action_rect,
                self.get_game_ui_button_state(
                    action_rect,
                    active=bool(selected_entry.get("actionEnabled")),
                    disabled=not bool(selected_entry.get("actionEnabled")),
                ),
            )
            self.blit_text_center(self.font_ui, action_label, action_rect.centerx, action_rect.top + 7, palette["text"])
            self.overlay_hotspots.append({"kind": "archive-action", "rect": action_rect})

        hint = "←→ 切换馆页 · ↑↓ 切换条目 · Enter 执行动作 · Esc 关闭"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 26, panel.bottom - 30))

    def get_archive_detail_image_asset_id(self, archive_key: str, entry: dict) -> str:
        if archive_key == "gallery":
            return str(entry.get("id") or "")
        return str(entry.get("previewAssetId") or "")

    def get_archive_detail_body(self, archive_key: str, entry: dict) -> str:
        title = str(entry.get("name") or "未命名条目")
        subtitle = str(entry.get("subtitle") or "")
        notes = str(entry.get("notes") or "")
        preview_text = str(entry.get("previewText") or "")
        speaker = str(entry.get("previewSpeakerName") or "")
        if archive_key == "gallery":
            return notes or preview_text or "这张 CG 已经解锁，可以在这里以大图方式查看。"
        if archive_key == "locations":
            return notes or preview_text or "这个地点来自剧情中的背景切换。"
        if archive_key == "characters":
            return notes or preview_text or f"{title} 已经收录进角色图鉴。"
        if archive_key == "narrations":
            return preview_text or notes or "这段旁白已经收录，可以在这里单独回看。"
        if archive_key == "relations":
            prefix = f"{speaker}：" if speaker else ""
            return f"{prefix}{preview_text or notes or subtitle or '这组关系已经在剧情中出现。'}"
        if archive_key == "achievements":
            return notes or subtitle or "这个成就已经点亮。"
        return preview_text or notes or subtitle or title

    def render_archive_detail_overlay(self) -> None:
        palette = self.get_active_palette()
        archive_key = self.archive_detail_key or self.current_archive_key
        entry = self.archive_detail_entry or self.get_selected_archive_entry() or {}
        panel = self.pygame.Rect(0, 0, min(self.width - 72, 1120), min(self.height - 92, 660))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 248), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 76), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")

        archive_title = ARCHIVE_MENU_ITEMS.get(archive_key, "资料馆")
        self.screen.blit(self.font_title.render(archive_title, True, palette["text"]), (panel.left + 28, panel.top + 24))
        self.screen.blit(
            self.font_ui.render("详情查看 · 这里展示条目的完整预览和说明", True, palette["muted"]),
            (panel.left + 28, panel.top + 60),
        )

        media_rect = self.pygame.Rect(panel.left + 28, panel.top + 100, int(panel.width * 0.54), panel.height - 172)
        content_rect = self.pygame.Rect(media_rect.right + 26, panel.top + 104, panel.right - media_rect.right - 54, panel.height - 182)
        image_asset_id = self.get_archive_detail_image_asset_id(archive_key, entry)
        empty_label = {
            "gallery": "CG 大图未加载",
            "locations": "地点预览未加载",
            "characters": "角色立绘未加载",
            "relations": "关系预览未加载",
            "narrations": "旁白摘录",
            "achievements": "成就详情",
        }.get(archive_key, "详情预览")
        self.render_contained_image(image_asset_id, media_rect, empty_label, palette)

        name = str(entry.get("name") or "未命名条目")
        subtitle = str(entry.get("subtitle") or "")
        self.screen.blit(self.font_title.render(name[:24], True, palette["text"]), (content_rect.left, content_rect.top))
        subtitle_y = content_rect.top + self.font_title.get_height() + 8
        if subtitle:
            self.blit_wrapped_text(
                self.font_ui,
                subtitle,
                self.pygame.Rect(content_rect.left, subtitle_y, content_rect.width, 44),
                palette["muted"],
                line_gap=4,
                max_lines=2,
            )

        body_top = subtitle_y + 58
        body_rect = self.pygame.Rect(content_rect.left, body_top, content_rect.width, max(80, content_rect.bottom - body_top - 82))
        self.blit_wrapped_text(self.font_body, self.get_archive_detail_body(archive_key, entry), body_rect, palette["text"], line_gap=8)

        meta_rows = []
        if archive_key == "characters":
            character = self.characters_by_id.get(str(entry.get("id") or "")) or {}
            expressions = character.get("expressions") or []
            meta_rows.append(f"表情数量：{len(expressions)}")
            meta_rows.append(f"默认站位：{character.get('defaultPosition') or 'center'}")
        elif archive_key == "gallery":
            meta_rows.append(f"CG ID：{entry.get('id') or 'unknown'}")
        elif archive_key == "achievements":
            meta_rows.append("状态：已点亮" if entry.get("unlocked") else "状态：未点亮")
        elif archive_key in {"narrations", "relations", "locations"}:
            meta_rows.append(f"来源：{subtitle or '剧情推进'}")

        meta_y = content_rect.bottom - 70
        for row in meta_rows[:2]:
            self.screen.blit(self.font_ui.render(row, True, palette["muted"]), (content_rect.left, meta_y))
            meta_y += 22

        back_rect = self.pygame.Rect(panel.right - 154, panel.bottom - 58, 126, 36)
        self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 74), back_rect, border_radius=14)
        self.pygame.draw.rect(self.screen, with_alpha(palette["accentAlt"], 84), back_rect, 1, border_radius=14)
        self.draw_game_ui_button_frame(back_rect, self.get_game_ui_button_state(back_rect, active=True))
        self.blit_text_center(self.font_ui, "返回资料馆", back_rect.centerx, back_rect.top + 9, palette["text"])
        self.overlay_hotspots.append({"kind": "archive-detail-back", "rect": back_rect})
        hint = "Enter / Esc 返回资料馆"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 44))

    def blit_text_center(self, font, text: str, center_x: int, top_y: int, color, target=None) -> None:
        target = target or self.screen
        surface = font.render(text, True, color)
        rect = surface.get_rect(midtop=(center_x, top_y))
        target.blit(surface, rect)

    def blit_wrapped_text(self, font, text: str, rect, color, line_gap: int = 6, max_lines: int | None = None) -> int:
        lines = wrap_text(font, str(text or ""), max(1, rect.width))
        if max_lines is not None:
            lines = lines[: max(0, max_lines)]
        y = rect.top
        line_height = font.get_height() + line_gap
        for line in lines:
            if y + font.get_height() > rect.bottom:
                break
            self.screen.blit(font.render(line, True, color), (rect.left, y))
            y += line_height
        return y

    def render_contained_image(self, asset_id: str | None, rect, empty_label: str, palette: dict) -> None:
        image = self._load_image(asset_id)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 36), rect, border_radius=22)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 28), rect, 1, border_radius=22)
        self.draw_game_ui_panel_frame(rect)
        if not image:
            self.blit_text_center(self.font_body, empty_label, rect.centerx, rect.centery - 18, palette["muted"])
            return
        image_width, image_height = image.get_size()
        scale = min(rect.width / max(1, image_width), rect.height / max(1, image_height))
        scaled = self.pygame.transform.smoothscale(
            image,
            (max(1, int(image_width * scale)), max(1, int(image_height * scale))),
        )
        image_rect = scaled.get_rect(center=rect.center)
        self.screen.blit(scaled, image_rect)

    def build_save_summary_line(self) -> str:
        quick_save = self.save_store.get("quickSave")
        formal_slots = self.save_store.get("formalSlots") or [None] * self.formal_save_slot_count
        filled_formal = sum(1 for item in formal_slots if item)
        quick_label = "已就绪" if quick_save else "空"
        return f"快存：{quick_label} · 正式存档：{filled_formal}/{self.formal_save_slot_count} · 存档文件：{self.save_file_path.name}"

    def handle_event(self, event) -> bool:
        if event.type == self.pygame.QUIT:
            return False
        if event.type == self.pygame.KEYDOWN and event.key == self.pygame.K_ESCAPE:
            if self.overlay_mode:
                if self.overlay_mode == "title":
                    return False
                if self.overlay_mode == "archive-detail":
                    self.close_archive_detail()
                    return True
                self.close_overlay()
                return True
            return False
        if event.type == self.pygame.KEYDOWN:
            if self.current_line and self.current_line.get("type") == "video_play" and event.key == self.pygame.K_v:
                self.open_current_video()
                return True
            if event.key == self.pygame.K_F11:
                self.toggle_display_mode()
                return True
            if self.overlay_mode == "title":
                return self.handle_overlay_event(event)
            if event.key in (self.pygame.K_F1, self.pygame.K_TAB):
                self.open_system_menu()
                return True
            if event.key == self.pygame.K_F6:
                self.open_save_dialog("save")
                return True
            if event.key == self.pygame.K_F7:
                self.open_save_dialog("load")
                return True
            if self.handle_save_shortcuts(event):
                return True
            if self.overlay_mode:
                return self.handle_overlay_event(event)

        if self.overlay_mode and event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_overlay_event(event)

        if self.current_choices:
            return self.handle_choice_event(event)

        if self.current_line and self.current_line.get("type") == "video_play" and event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_video_card_mouse_event(event)

        if self.current_line or self.finished:
            if event.type == self.pygame.KEYDOWN and event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                if self.finished:
                    return False
                self.advance_current_line_if_allowed()
            elif event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.finished:
                    return False
                self.advance_current_line_if_allowed()
        return True

    def handle_overlay_event(self, event) -> bool:
        if self.overlay_mode == "title":
            return self.handle_title_overlay_event(event)
        if self.overlay_mode in {"save", "load"}:
            return self.handle_save_dialog_event(event)
        if self.overlay_mode == "system":
            return self.handle_system_menu_event(event)
        if self.overlay_mode == "profile":
            return self.handle_profile_overlay_event(event)
        if self.overlay_mode == "auto-resume":
            return self.handle_auto_resume_overlay_event(event)
        if self.overlay_mode == "settings":
            return self.handle_settings_overlay_event(event)
        if self.overlay_mode == "archives":
            return self.handle_archive_overlay_event(event)
        if self.overlay_mode == "archive-detail":
            return self.handle_archive_detail_overlay_event(event)
        return True

    def handle_title_overlay_event(self, event) -> bool:
        pygame = self.pygame
        menu_items = self.get_title_menu_items()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.title_menu_index = (self.title_menu_index - 1) % len(menu_items)
                return True
            if event.key == pygame.K_DOWN:
                self.title_menu_index = (self.title_menu_index + 1) % len(menu_items)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_title_menu_item(str(menu_items[self.title_menu_index]["key"]))
            shortcut_map = {
                pygame.K_n: "start",
                pygame.K_r: "resume",
                pygame.K_l: "load",
                pygame.K_s: "settings",
                pygame.K_a: "archives",
            }
            if event.key in shortcut_map:
                return self.activate_title_menu_item(shortcut_map[event.key])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target.get("kind") == "title-item" and target["rect"].collidepoint(event.pos):
                    for index, item in enumerate(menu_items):
                        if item["key"] == target.get("value"):
                            self.title_menu_index = index
                            break
                    return self.activate_title_menu_item(str(target.get("value") or "start"))
        return True

    def handle_save_dialog_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.change_save_dialog_page(-1)
                return True
            if event.key == pygame.K_RIGHT:
                self.change_save_dialog_page(1)
                return True
            if event.key == pygame.K_UP:
                self.overlay_focus_index = (self.overlay_focus_index - 2) % max(1, self.get_save_dialog_slot_count())
                self.normalize_overlay_focus()
                return True
            if event.key == pygame.K_DOWN:
                self.overlay_focus_index = (self.overlay_focus_index + 2) % max(1, self.get_save_dialog_slot_count())
                self.normalize_overlay_focus()
                return True
            if event.key == pygame.K_a:
                self.overlay_focus_index = max(0, self.overlay_focus_index - 1)
                return True
            if event.key == pygame.K_d:
                self.overlay_focus_index = min(max(0, self.get_save_dialog_slot_count() - 1), self.overlay_focus_index + 1)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate_overlay_slot(self.overlay_focus_index)
                return True
            digit_map = {
                pygame.K_1: 0,
                pygame.K_2: 1,
                pygame.K_3: 2,
                pygame.K_4: 3,
                pygame.K_5: 4,
                pygame.K_6: 5,
            }
            if event.key in digit_map:
                self.activate_overlay_slot(digit_map[event.key])
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target["rect"].collidepoint(event.pos):
                    kind = target.get("kind")
                    if kind == "slot":
                        self.activate_overlay_slot(int(target.get("value", 0)))
                    elif kind == "prev":
                        self.change_save_dialog_page(-1)
                    elif kind == "next":
                        self.change_save_dialog_page(1)
                    elif kind == "switch":
                        self.open_save_dialog("load" if self.overlay_mode == "save" else "save")
                    elif kind == "close":
                        self.close_overlay()
                    return True
        return True

    def handle_system_menu_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.system_menu_index = (self.system_menu_index - 1) % len(SYSTEM_MENU_ITEMS)
                return True
            if event.key == pygame.K_DOWN:
                self.system_menu_index = (self.system_menu_index + 1) % len(SYSTEM_MENU_ITEMS)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_system_menu_item(SYSTEM_MENU_ITEMS[self.system_menu_index][0])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target["kind"] == "system-item" and target["rect"].collidepoint(event.pos):
                    return self.activate_system_menu_item(str(target["value"]))
        return True

    def handle_profile_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.close_overlay()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target.get("kind") == "close" and target["rect"].collidepoint(event.pos):
                    self.close_overlay()
                    return True
        return True

    def handle_auto_resume_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.load_auto_resume_snapshot()
                return True
            if event.key == pygame.K_c:
                self.clear_auto_resume_snapshot()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if not target["rect"].collidepoint(event.pos):
                    continue
                kind = target.get("kind")
                if kind == "auto-resume-load":
                    self.load_auto_resume_snapshot()
                    return True
                if kind == "auto-resume-clear":
                    self.clear_auto_resume_snapshot()
                    return True
                if kind == "close":
                    self.close_overlay()
                    return True
        return True

    def handle_settings_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.settings_menu_index = (self.settings_menu_index - 1) % len(SETTINGS_MENU_ITEMS)
                return True
            if event.key == pygame.K_DOWN:
                self.settings_menu_index = (self.settings_menu_index + 1) % len(SETTINGS_MENU_ITEMS)
                return True
            if event.key == pygame.K_LEFT:
                self.adjust_runtime_setting(SETTINGS_MENU_ITEMS[self.settings_menu_index][0], -1)
                return True
            if event.key == pygame.K_RIGHT:
                self.adjust_runtime_setting(SETTINGS_MENU_ITEMS[self.settings_menu_index][0], 1)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.adjust_runtime_setting(SETTINGS_MENU_ITEMS[self.settings_menu_index][0], 1)
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, target in enumerate(self.overlay_hotspots):
                if target["kind"] == "settings-item" and target["rect"].collidepoint(event.pos):
                    self.settings_menu_index = index
                    midpoint = target["rect"].centerx
                    self.adjust_runtime_setting(str(target["value"]), -1 if event.pos[0] < midpoint else 1)
                    return True
        return True

    def handle_archive_overlay_event(self, event) -> bool:
        pygame = self.pygame
        entries = self.get_archive_entries(self.current_archive_key)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.change_archive_tab(-1)
                return True
            if event.key == pygame.K_RIGHT:
                self.change_archive_tab(1)
                return True
            if event.key == pygame.K_UP and entries:
                self.archive_selection_index = (self.archive_selection_index - 1) % len(entries)
                return True
            if event.key == pygame.K_DOWN and entries:
                self.archive_selection_index = (self.archive_selection_index + 1) % len(entries)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_archive_entry(self.get_selected_archive_entry())
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target["rect"].collidepoint(event.pos):
                    if target["kind"] == "archive-tab":
                        self.current_archive_key = str(target.get("value") or "chapters")
                        self.archive_selection_index = 0
                        return True
                    if target["kind"] == "archive-item":
                        self.archive_selection_index = int(target.get("value", 0))
                        return True
                    if target["kind"] == "archive-action":
                        return self.activate_archive_entry(self.get_selected_archive_entry())
        return True

    def handle_archive_detail_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.close_archive_detail()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target.get("kind") == "archive-detail-back" and target["rect"].collidepoint(event.pos):
                    self.close_archive_detail()
                    return True
        return True

    def handle_save_shortcuts(self, event) -> bool:
        pygame = self.pygame
        if event.key == pygame.K_F5:
            self.save_quick()
            return True
        if event.key in (pygame.K_F8, pygame.K_F9):
            self.load_quick()
            return True

        is_ctrl = bool(event.mod & pygame.KMOD_CTRL) or bool(event.mod & pygame.KMOD_META)
        if not is_ctrl:
            return False

        slot_keys = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
        }
        if event.key not in slot_keys:
            return False

        slot_index = slot_keys[event.key]
        if event.mod & pygame.KMOD_SHIFT:
            self.load_formal_slot(slot_index)
        else:
            self.save_formal_slot(slot_index)
        return True

    def handle_choice_event(self, event) -> bool:
        if not self.current_choices:
            return True
        if event.type == self.pygame.KEYDOWN:
            if event.key == self.pygame.K_UP:
                self.current_choice_index = (self.current_choice_index - 1) % len(self.current_choices)
            elif event.key == self.pygame.K_DOWN:
                self.current_choice_index = (self.current_choice_index + 1) % len(self.current_choices)
            elif event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                self.choose_current_option(self.current_choice_index)
        elif event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            panel = self.get_dialog_panel_rect(max(212, 86 + len(self.current_choices) * 54))
            padding_x = int(self.dialog_box_config.get("paddingX", 18))
            padding_y = int(self.dialog_box_config.get("paddingY", 14))
            button_top = panel.top + padding_y + self.font_title.get_height() + 18
            button_width = panel.width - padding_x * 2
            for index, _option in enumerate(self.current_choices):
                row_rect = self.pygame.Rect(panel.left + padding_x, button_top + index * 52, button_width, 40)
                if row_rect.collidepoint(event.pos):
                    self.current_choice_index = index
                    self.choose_current_option(index)
                    break
        return True

    def run(self) -> int:
        running = True
        while running:
            dt_seconds = self.clock.tick(FPS) / 1000
            self.runtime_elapsed_seconds += dt_seconds
            for event in self.pygame.event.get():
                running = self.handle_event(event)
                if not running:
                    break
            self.update_stage_visual_effects(dt_seconds)
            self.update_particle_effect(dt_seconds)
            self.render()

        self.record_player_session_end()
        self.persist_auto_resume_snapshot()
        self.stop_bgm()
        self.stop_voice()
        return 0


def run_player(game_data_path: Path) -> int:
    try:
        import pygame
    except ImportError:
        bundle_dir = game_data_path.resolve().parent
        requirements_name = (
            "requirements-native-runtime.txt"
            if (bundle_dir / "requirements-native-runtime.txt").is_file()
            else "requirements.txt"
        )
        print("缺少依赖：pygame-ce")
        print(f"请先运行：python3 -m pip install -r {requirements_name}")
        return 1

    try:
        pygame.init()
        player = NativeRuntimePlayer(pygame, game_data_path)
        return player.run()
    except NativeRuntimeError as error:
        log_path = write_runtime_crash_log(game_data_path, error, "native_runtime_error")
        print(f"原生 Runtime 包无法启动：{error}")
        print(f"错误日志：{log_path}")
        show_runtime_error_screen(pygame, str(error), log_path)
        return 1
    except Exception as error:
        log_path = write_runtime_crash_log(game_data_path, error, "unexpected_error")
        print(f"原生 Runtime 包发生未处理错误：{error}")
        print(f"错误日志：{log_path}")
        show_runtime_error_screen(pygame, f"{type(error).__name__}: {error}", log_path)
        return 1
    finally:
        try:
            pygame.quit()
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tony Na Engine 原生 Runtime 播放器")
    parser.add_argument("game_data", nargs="?", default=DEFAULT_GAME_DATA_NAME, help="导出的 game_data.json 路径")
    parser.add_argument("--validate-bundle", dest="validate_bundle", help="只检查导出包结构，不启动窗口")
    parser.add_argument("--release-check", dest="release_check", help="输出发布前自检报告 JSON，不启动窗口")
    parser.add_argument("--exercise-save-load", dest="exercise_save_load", help="检查存档文件能否写入和读回")
    parser.add_argument("--exercise-settings", dest="exercise_settings", help="检查原生 Runtime 设置能否写入和读回")
    parser.add_argument("--exercise-archives", dest="exercise_archives", help="检查原生 Runtime 资料馆进度能否写入和读回")
    parser.add_argument("--exercise-particles", dest="exercise_particles", help="检查原生 Runtime 粒子配置能否生成可播放条目")
    parser.add_argument("--exercise-visual-effects", dest="exercise_visual_effects", help="检查原生 Runtime 高级演出配置能否规范化")
    parser.add_argument("--exercise-profile", dest="exercise_profile", help="检查原生 Runtime 玩家档案和续玩记录能否写入和读回")
    parser.add_argument("--describe-title-screen", dest="describe_title_screen", help="输出原生 Runtime 标题页配置摘要，不启动窗口")
    parser.add_argument("--describe-video-bridge", dest="describe_video_bridge", help="输出原生 Runtime 视频桥接摘要，不启动窗口")
    parser.add_argument("--describe-video-backends", dest="describe_video_backends", help="输出原生 Runtime 可选视频后端摘要，不启动窗口")
    parser.add_argument("--probe-video-preview", dest="probe_video_preview", help="输出原生 Runtime 可选视频帧预览探针，不启动窗口")
    parser.add_argument("--describe-save-dialog", dest="describe_save_dialog", help="输出正式存档面板摘要，不启动窗口")
    parser.add_argument("--page", dest="save_dialog_page", type=int, default=0, help="配合 --describe-save-dialog 使用，指定页码")
    args = parser.parse_args(argv)

    if args.validate_bundle:
        try:
            validate_bundle(Path(args.validate_bundle).resolve())
            print("Native runtime bundle validation passed.")
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime bundle validation failed: {error}")
            return 1

    if args.release_check:
        print_release_check_report(Path(args.release_check).resolve())
        return 0

    if args.exercise_save_load:
        try:
            exercise_save_load(Path(args.exercise_save_load).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime save/load validation failed: {error}")
            return 1

    if args.exercise_settings:
        try:
            exercise_runtime_settings(Path(args.exercise_settings).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime settings validation failed: {error}")
            return 1

    if args.exercise_archives:
        try:
            exercise_archive_progress(Path(args.exercise_archives).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime archive validation failed: {error}")
            return 1

    if args.exercise_particles:
        try:
            exercise_particle_effect(Path(args.exercise_particles).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime particle validation failed: {error}")
            return 1

    if args.exercise_visual_effects:
        try:
            exercise_visual_effects(Path(args.exercise_visual_effects).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime visual effects validation failed: {error}")
            return 1

    if args.exercise_profile:
        try:
            exercise_player_profile(Path(args.exercise_profile).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime profile validation failed: {error}")
            return 1

    if args.describe_title_screen:
        try:
            print_native_title_screen_report(Path(args.describe_title_screen).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime title screen description failed: {error}")
            return 1

    if args.describe_video_bridge:
        try:
            print_native_video_bridge_report(Path(args.describe_video_bridge).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime video bridge description failed: {error}")
            return 1

    if args.describe_video_backends:
        try:
            print_native_video_backend_report(Path(args.describe_video_backends).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime video backend description failed: {error}")
            return 1

    if args.probe_video_preview:
        try:
            print_native_video_preview_probe_report(Path(args.probe_video_preview).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime video preview probe failed: {error}")
            return 1

    if args.describe_save_dialog:
        try:
            describe_save_dialog(Path(args.describe_save_dialog).resolve(), page=args.save_dialog_page)
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime save dialog description failed: {error}")
            return 1

    return run_player(resolve_game_data_argument(args.game_data))


if __name__ == "__main__":
    raise SystemExit(main())
