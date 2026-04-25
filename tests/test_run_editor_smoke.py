from __future__ import annotations

import base64
import copy
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import tarfile
import unittest
from pathlib import Path

import run_editor


def build_upload_payload(name: str, raw: bytes) -> dict:
    return {
        "name": name,
        "dataBase64": base64.b64encode(raw).decode("utf-8"),
    }


def build_fake_wav_bytes() -> bytes:
    return (
        b"RIFF"
        b"\x24\x00\x00\x00"
        b"WAVE"
        b"fmt "
        b"\x10\x00\x00\x00"
        b"\x01\x00"
        b"\x01\x00"
        b"\x44\xac\x00\x00"
        b"\x88\x58\x01\x00"
        b"\x02\x00"
        b"\x10\x00"
        b"data"
        b"\x00\x00\x00\x00"
    )


def build_fake_png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
    )


def create_fake_runtime_archive(archive_path: Path, platform_key: str) -> Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "python"
        if platform_key == run_editor.EDITOR_PLATFORM_WINDOWS:
            executable = root / "python.exe"
        else:
            executable = root / "bin" / "python3"
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("fake-python", encoding="utf-8")
        if platform_key != run_editor.EDITOR_PLATFORM_WINDOWS:
            executable.chmod(0o755)

        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(root, arcname="python")
    return archive_path


def create_fake_nwjs_runtime_dir(runtime_dir: Path, platform_key: str) -> Path:
    config = run_editor.get_nwjs_runtime_config(platform_key)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    if platform_key == run_editor.NWJS_GAME_PLATFORM_MACOS:
        app_bundle = runtime_dir / str(config.get("appBundleName") or "nwjs.app")
        (app_bundle / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
        (app_bundle / "Contents" / "Resources").mkdir(parents=True, exist_ok=True)
        executable_path = app_bundle / "Contents" / "MacOS" / "nwjs"
        executable_path.write_text("fake-nwjs", encoding="utf-8")
        executable_path.chmod(0o755)
        with (app_bundle / "Contents" / "Info.plist").open("wb") as plist_file:
            plistlib.dump({"CFBundleExecutable": "nwjs", "CFBundleName": "nwjs"}, plist_file)
        return runtime_dir

    for file_name in config.get("requiredFiles") or []:
        file_path = runtime_dir / str(file_name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("fake-runtime", encoding="utf-8")
        if file_path.name in {"nw", "nw.exe"}:
            file_path.chmod(0o755)
    for dir_name in config.get("requiredDirs") or []:
        (runtime_dir / str(dir_name)).mkdir(parents=True, exist_ok=True)
    return runtime_dir


def create_fake_iscc_script(script_path: Path) -> Path:
    script_path.write_text(
        """#!/bin/sh
set -eu
output_dir=""
output_base="TonyNaEngineEditorSetup"
for arg in "$@"; do
  case "$arg" in
    /O*) output_dir="${arg#/O}" ;;
    /F*) output_base="${arg#/F}" ;;
  esac
done
if [ -z "$output_dir" ]; then
  output_dir="$(pwd)"
fi
mkdir -p "$output_dir"
printf 'fake-windows-installer' > "$output_dir/$output_base.exe"
""",
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    return script_path


def create_fake_signtool_script(script_path: Path) -> Path:
    script_path.write_text(
        """#!/bin/sh
set -eu
exit 0
""",
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    return script_path


class RunEditorSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)
        self.sample_dir = self.test_root / "template_project"
        shutil.copytree(run_editor.ROOT_DIR / "template_project", self.sample_dir)
        self.projects_dir = self.test_root / "projects"
        self.exports_dir = self.test_root / "exports"
        self.runtime_cache_dir = self.test_root / ".export_runtime_cache"
        self.local_runtime_dirs = [
            self.test_root / "desktop_runtime",
            self.test_root / "desktop_runtime" / "windows",
        ]
        self.fake_nwjs_runtime_dirs = {
            run_editor.NWJS_GAME_PLATFORM_WINDOWS: create_fake_nwjs_runtime_dir(
                self.test_root / "fake_nwjs_windows_runtime",
                run_editor.NWJS_GAME_PLATFORM_WINDOWS,
            ),
            run_editor.NWJS_GAME_PLATFORM_MACOS: create_fake_nwjs_runtime_dir(
                self.test_root / "fake_nwjs_macos_runtime",
                run_editor.NWJS_GAME_PLATFORM_MACOS,
            ),
            run_editor.NWJS_GAME_PLATFORM_LINUX: create_fake_nwjs_runtime_dir(
                self.test_root / "fake_nwjs_linux_runtime",
                run_editor.NWJS_GAME_PLATFORM_LINUX,
            ),
        }
        self.portable_runtime_archives = {
            run_editor.EDITOR_PLATFORM_MACOS: create_fake_runtime_archive(
                self.test_root / "fake_macos_runtime.tar.gz",
                run_editor.EDITOR_PLATFORM_MACOS,
            ),
            run_editor.EDITOR_PLATFORM_WINDOWS: create_fake_runtime_archive(
                self.test_root / "fake_windows_runtime.tar.gz",
                run_editor.EDITOR_PLATFORM_WINDOWS,
            ),
            run_editor.EDITOR_PLATFORM_LINUX: create_fake_runtime_archive(
                self.test_root / "fake_linux_runtime.tar.gz",
                run_editor.EDITOR_PLATFORM_LINUX,
            ),
        }
        self.fake_iscc = create_fake_iscc_script(self.test_root / "fake_iscc.sh")
        self.fake_signtool = create_fake_signtool_script(self.test_root / "fake_signtool.sh")

        self.original_globals = {
            "PROJECTS_DIR": run_editor.PROJECTS_DIR,
            "SAMPLE_PROJECT_DIR": run_editor.SAMPLE_PROJECT_DIR,
            "EXPORTS_DIR": run_editor.EXPORTS_DIR,
            "EXPORT_RUNTIME_CACHE_DIR": run_editor.EXPORT_RUNTIME_CACHE_DIR,
            "LOCAL_NWJS_RUNTIME_DIRS": run_editor.LOCAL_NWJS_RUNTIME_DIRS,
            "TEMPLATE_DIR": run_editor.TEMPLATE_DIR,
            "DATA_DIR": run_editor.DATA_DIR,
            "CHAPTERS_DIR": run_editor.CHAPTERS_DIR,
            "PROJECT_PATH": run_editor.PROJECT_PATH,
            "CURRENT_PROJECT_INFO": dict(run_editor.CURRENT_PROJECT_INFO),
            "HAS_SELECTED_PROJECT": run_editor.HAS_SELECTED_PROJECT,
        }
        self.original_env = {
            run_editor.get_portable_runtime_override_env_var(platform_key): os.environ.get(
                run_editor.get_portable_runtime_override_env_var(platform_key)
            )
            for platform_key in self.portable_runtime_archives
        }
        self.original_env.update(
            {
                run_editor.get_nwjs_runtime_dir_override_env_var(platform_key): os.environ.get(
                    run_editor.get_nwjs_runtime_dir_override_env_var(platform_key)
                )
                for platform_key in self.fake_nwjs_runtime_dirs
            }
        )
        self.original_env[run_editor.EDITOR_WINDOWS_ISCC_ENV] = os.environ.get(run_editor.EDITOR_WINDOWS_ISCC_ENV)
        self.original_env[run_editor.EDITOR_WINDOWS_SIGNTOOL_ENV] = os.environ.get(run_editor.EDITOR_WINDOWS_SIGNTOOL_ENV)
        self.original_env[run_editor.EDITOR_WINDOWS_CERT_SUBJECT_ENV] = os.environ.get(
            run_editor.EDITOR_WINDOWS_CERT_SUBJECT_ENV
        )

        run_editor.PROJECTS_DIR = self.projects_dir
        run_editor.SAMPLE_PROJECT_DIR = self.sample_dir
        run_editor.EXPORTS_DIR = self.exports_dir
        run_editor.EXPORT_RUNTIME_CACHE_DIR = self.runtime_cache_dir
        run_editor.LOCAL_NWJS_RUNTIME_DIRS = self.local_runtime_dirs
        run_editor.TEMPLATE_DIR = self.sample_dir
        run_editor.DATA_DIR = self.sample_dir / "data"
        run_editor.CHAPTERS_DIR = run_editor.DATA_DIR / "chapters"
        run_editor.PROJECT_PATH = self.sample_dir / "project.json"
        run_editor.CURRENT_PROJECT_INFO = {
            "projectId": run_editor.SAMPLE_PROJECT_ID,
            "kind": "sample",
            "projectDir": str(self.sample_dir),
        }
        run_editor.HAS_SELECTED_PROJECT = False
        for platform_key, archive_path in self.portable_runtime_archives.items():
            os.environ[run_editor.get_portable_runtime_override_env_var(platform_key)] = str(archive_path)
        for platform_key, runtime_dir in self.fake_nwjs_runtime_dirs.items():
            os.environ[run_editor.get_nwjs_runtime_dir_override_env_var(platform_key)] = str(runtime_dir)
        os.environ[run_editor.EDITOR_WINDOWS_ISCC_ENV] = str(self.fake_iscc)
        os.environ[run_editor.EDITOR_WINDOWS_SIGNTOOL_ENV] = str(self.fake_signtool)
        os.environ[run_editor.EDITOR_WINDOWS_CERT_SUBJECT_ENV] = "Tony Na Engine Project"

    def tearDown(self) -> None:
        run_editor.PROJECTS_DIR = self.original_globals["PROJECTS_DIR"]
        run_editor.SAMPLE_PROJECT_DIR = self.original_globals["SAMPLE_PROJECT_DIR"]
        run_editor.EXPORTS_DIR = self.original_globals["EXPORTS_DIR"]
        run_editor.EXPORT_RUNTIME_CACHE_DIR = self.original_globals["EXPORT_RUNTIME_CACHE_DIR"]
        run_editor.LOCAL_NWJS_RUNTIME_DIRS = self.original_globals["LOCAL_NWJS_RUNTIME_DIRS"]
        run_editor.TEMPLATE_DIR = self.original_globals["TEMPLATE_DIR"]
        run_editor.DATA_DIR = self.original_globals["DATA_DIR"]
        run_editor.CHAPTERS_DIR = self.original_globals["CHAPTERS_DIR"]
        run_editor.PROJECT_PATH = self.original_globals["PROJECT_PATH"]
        run_editor.CURRENT_PROJECT_INFO = self.original_globals["CURRENT_PROJECT_INFO"]
        run_editor.HAS_SELECTED_PROJECT = self.original_globals["HAS_SELECTED_PROJECT"]
        for env_key, env_value in self.original_env.items():
            if env_value is None:
                os.environ.pop(env_key, None)
            else:
                os.environ[env_key] = env_value
        self.temp_dir.cleanup()

    def create_blank_project_with_chapter(self) -> tuple[dict, dict]:
        run_editor.create_blank_project("自动化测试项目")
        chapter_result = run_editor.create_chapter("第一章", "开场")
        return run_editor.get_current_project_summary(), chapter_result

    def save_scene_with_blocks(self, chapter_id: str, scene: dict, blocks: list[dict]) -> dict:
        updated_scene = copy.deepcopy(scene)
        updated_scene["blocks"] = blocks
        run_editor.save_scene(chapter_id, updated_scene["id"], updated_scene)
        return updated_scene

    def test_project_creation_scene_save_and_settings(self) -> None:
        project_summary, chapter_result = self.create_blank_project_with_chapter()

        self.assertEqual(project_summary["title"], "自动化测试项目")
        self.assertEqual(project_summary["editorMode"], "beginner")

        updated_scene = self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "你好，欢迎来到自动化测试。",
                }
            ],
        )

        result = run_editor.save_project_settings(
            resolution={"width": 1920, "height": 1080},
            release_version="1.2.3-beta",
            editor_mode="advanced",
            runtime_settings={"formalSaveSlotCount": 60},
            dialog_box_config={
                "preset": "transparent",
                "shape": "capsule",
                "widthPercent": 82,
                "minHeight": 132,
                "backgroundColor": "#10243a",
                "backgroundOpacity": 12,
                "borderColor": "#6fdfff",
                "borderOpacity": 0,
                "textColor": "#f0f6ff",
                "speakerColor": "#ffffff",
                "panelAssetFit": "contain",
                "anchor": "center",
                "offsetXPercent": 12,
                "offsetYPercent": -8,
            },
            game_ui_config={
                "preset": "minimal",
                "layoutPreset": "cinematic",
                "titleLayout": "poster",
                "fontStyle": "serif",
                "surfaceStyle": "minimal",
                "brandMode": "hidden",
                "sidePanelMode": "hidden",
                "sidePanelPosition": "left",
                "topbarPosition": "bottom",
                "hudPosition": "bottom-right",
                "titleCardAnchor": "right",
                "titleCardOffsetXPercent": -7,
                "titleCardOffsetYPercent": 5,
                "layoutGap": 26,
                "sidePanelWidth": 356,
                "backgroundColor": "#05070c",
                "backgroundAccentColor": "#ffffff",
                "panelColor": "#080a10",
                "panelOpacity": 48,
                "textColor": "#f7f7f7",
                "mutedTextColor": "#c6c8cf",
                "accentColor": "#ffffff",
                "accentAltColor": "#aeb5c6",
                "buttonTextColor": "#101216",
                "borderColor": "#ffffff",
                "borderOpacity": 16,
                "cornerRadius": 10,
                "backdropBlur": 2,
                "stageVignette": 20,
                "motionIntensity": 10,
                "titleBackgroundAssetId": "asset_title_bg",
                "titleBackgroundFit": "contain",
                "titleBackgroundOpacity": 55,
                "titleLogoAssetId": "asset_title_logo",
                "panelFrameAssetId": "asset_panel_frame",
                "panelFrameOpacity": 41,
                "panelFrameSlice": {"top": 12, "right": 18, "bottom": 20, "left": 14},
                "buttonFrameAssetId": "asset_button_frame",
                "buttonHoverFrameAssetId": "asset_button_hover",
                "buttonPressedFrameAssetId": "asset_button_pressed",
                "buttonDisabledFrameAssetId": "asset_button_disabled",
                "buttonFrameOpacity": 36,
                "buttonFrameSlice": {"top": 8, "right": 16, "bottom": 10, "left": 16},
                "saveSlotFrameAssetId": "asset_save_frame",
                "systemPanelFrameAssetId": "asset_system_frame",
                "uiOverlayAssetId": "asset_overlay_grid",
                "uiOverlayOpacity": 9,
            },
            particle_custom_presets=[
                {
                    "name": "暴雪测试",
                    "config": {
                        "action": "start",
                        "preset": "snow",
                        "density": 48,
                    },
                }
            ],
        )

        bundle = run_editor.load_project_bundle()
        saved_scene = bundle["chapters"][0]["scenes"][0]
        saved_project = bundle["project"]

        self.assertEqual(saved_scene["id"], updated_scene["id"])
        self.assertEqual(saved_scene["blocks"][0]["text"], "你好，欢迎来到自动化测试。")
        self.assertEqual(result["project"]["releaseVersion"], "1.2.3-beta")
        self.assertEqual(saved_project["editorMode"], "advanced")
        self.assertEqual(saved_project["resolution"]["width"], 1920)
        self.assertEqual(saved_project["runtimeSettings"]["formalSaveSlotCount"], 60)
        self.assertEqual(saved_project["dialogBoxConfig"]["preset"], "transparent")
        self.assertEqual(saved_project["dialogBoxConfig"]["shape"], "capsule")
        self.assertEqual(saved_project["dialogBoxConfig"]["widthPercent"], 82)
        self.assertEqual(saved_project["dialogBoxConfig"]["backgroundColor"], "#10243a")
        self.assertEqual(saved_project["dialogBoxConfig"]["anchor"], "center")
        self.assertEqual(saved_project["dialogBoxConfig"]["offsetXPercent"], 12)
        self.assertEqual(saved_project["dialogBoxConfig"]["offsetYPercent"], -8)
        self.assertEqual(saved_project["gameUiConfig"]["preset"], "minimal")
        self.assertEqual(saved_project["gameUiConfig"]["layoutPreset"], "cinematic")
        self.assertEqual(saved_project["gameUiConfig"]["titleLayout"], "poster")
        self.assertEqual(saved_project["gameUiConfig"]["fontStyle"], "serif")
        self.assertEqual(saved_project["gameUiConfig"]["brandMode"], "hidden")
        self.assertEqual(saved_project["gameUiConfig"]["sidePanelMode"], "hidden")
        self.assertEqual(saved_project["gameUiConfig"]["sidePanelPosition"], "left")
        self.assertEqual(saved_project["gameUiConfig"]["topbarPosition"], "bottom")
        self.assertEqual(saved_project["gameUiConfig"]["hudPosition"], "bottom-right")
        self.assertEqual(saved_project["gameUiConfig"]["titleCardAnchor"], "right")
        self.assertEqual(saved_project["gameUiConfig"]["titleCardOffsetXPercent"], -7)
        self.assertEqual(saved_project["gameUiConfig"]["titleCardOffsetYPercent"], 5)
        self.assertEqual(saved_project["gameUiConfig"]["layoutGap"], 26)
        self.assertEqual(saved_project["gameUiConfig"]["sidePanelWidth"], 356)
        self.assertEqual(saved_project["gameUiConfig"]["panelOpacity"], 48)
        self.assertEqual(saved_project["gameUiConfig"]["titleBackgroundAssetId"], "asset_title_bg")
        self.assertEqual(saved_project["gameUiConfig"]["titleBackgroundFit"], "contain")
        self.assertEqual(saved_project["gameUiConfig"]["titleBackgroundOpacity"], 55)
        self.assertEqual(saved_project["gameUiConfig"]["titleLogoAssetId"], "asset_title_logo")
        self.assertEqual(saved_project["gameUiConfig"]["panelFrameAssetId"], "asset_panel_frame")
        self.assertEqual(saved_project["gameUiConfig"]["panelFrameOpacity"], 41)
        self.assertEqual(saved_project["gameUiConfig"]["panelFrameSlice"], {"top": 12, "right": 18, "bottom": 20, "left": 14})
        self.assertEqual(saved_project["gameUiConfig"]["buttonFrameAssetId"], "asset_button_frame")
        self.assertEqual(saved_project["gameUiConfig"]["buttonHoverFrameAssetId"], "asset_button_hover")
        self.assertEqual(saved_project["gameUiConfig"]["buttonPressedFrameAssetId"], "asset_button_pressed")
        self.assertEqual(saved_project["gameUiConfig"]["buttonDisabledFrameAssetId"], "asset_button_disabled")
        self.assertEqual(saved_project["gameUiConfig"]["buttonFrameOpacity"], 36)
        self.assertEqual(saved_project["gameUiConfig"]["buttonFrameSlice"], {"top": 8, "right": 16, "bottom": 10, "left": 16})
        self.assertEqual(saved_project["gameUiConfig"]["saveSlotFrameAssetId"], "asset_save_frame")
        self.assertEqual(saved_project["gameUiConfig"]["systemPanelFrameAssetId"], "asset_system_frame")
        self.assertEqual(saved_project["gameUiConfig"]["uiOverlayAssetId"], "asset_overlay_grid")
        self.assertEqual(saved_project["gameUiConfig"]["uiOverlayOpacity"], 9)
        self.assertEqual(saved_project["particleCustomPresets"][0]["name"], "暴雪测试")

    def test_asset_import_replace_and_delete_with_usage_protection(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        import_result = run_editor.import_assets(
            "background",
            [build_upload_payload("bg_classroom.png", b"fake-image-1")],
        )
        asset = import_result["assets"][0]

        self.assertEqual(asset["type"], "background")
        self.assertTrue((run_editor.TEMPLATE_DIR / asset["path"]).is_file())

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "background",
                    "assetId": asset["id"],
                    "transition": "fade",
                }
            ],
        )

        with self.assertRaisesRegex(ValueError, "还在被使用|先解除引用"):
            run_editor.delete_asset(asset["id"])

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "narration",
                    "text": "背景引用已经解除。",
                }
            ],
        )

        replace_result = run_editor.replace_asset_file(
            asset["id"],
            build_upload_payload("bg_evening.png", b"fake-image-2"),
        )
        self.assertTrue((run_editor.TEMPLATE_DIR / replace_result["asset"]["path"]).is_file())

        delete_result = run_editor.delete_asset(asset["id"])
        self.assertEqual(delete_result["deletedAssetId"], asset["id"])
        self.assertFalse((run_editor.TEMPLATE_DIR / replace_result["asset"]["path"]).exists())

    def test_video_blocks_export_to_web_runtime(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        import_result = run_editor.import_assets(
            "auto",
            [build_upload_payload("opening_movie.mp4", b"fake-video-data")],
        )
        video_asset = import_result["assets"][0]
        self.assertEqual(video_asset["type"], "video")
        self.assertTrue(video_asset["path"].startswith("assets/video/"))

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_video",
                    "type": "video_play",
                    "assetId": video_asset["id"],
                    "title": "Opening Movie",
                    "fit": "contain",
                    "volume": 75,
                    "startTimeSeconds": 1.5,
                    "endTimeSeconds": 4,
                    "skippable": True,
                },
                {
                    "id": "block_credits",
                    "type": "credits_roll",
                    "title": "STAFF",
                    "subtitle": "Thank you for playing",
                    "lines": ["企划：Tony Na", "测试：Tony Na Engine"],
                    "durationSeconds": 12,
                    "background": "dark",
                    "skippable": True,
                },
            ],
        )

        export_result = run_editor.export_web_build()
        build_dir = Path(export_result["buildPath"])
        exported_video = build_dir / "assets" / "video" / f"{video_asset['id']}.mp4"
        index_html = (build_dir / "index.html").read_text(encoding="utf-8")

        self.assertTrue(exported_video.is_file())
        self.assertIn('"type": "video_play"', index_html)
        self.assertIn('"type": "credits_roll"', index_html)
        self.assertIn("Opening Movie", index_html)

    def test_video_blocks_export_to_native_runtime_bridge(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        import_result = run_editor.import_assets(
            "auto",
            [build_upload_payload("opening_movie.mp4", b"fake-video-data")],
        )
        video_asset = import_result["assets"][0]

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_video",
                    "type": "video_play",
                    "assetId": video_asset["id"],
                    "title": "Opening Movie",
                    "fit": "contain",
                    "volume": 75,
                    "startTimeSeconds": 1.5,
                    "endTimeSeconds": 4,
                    "skippable": True,
                },
                {
                    "id": "block_after_video",
                    "type": "narration",
                    "text": "视频之后继续剧情。",
                },
            ],
        )

        export_result = run_editor.export_native_runtime_build()
        build_dir = Path(export_result["buildPath"])

        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        self.assertEqual(release_check_payload["status"], "warn")
        self.assertTrue(
            {"video_native_external_player_bridge", "video_native_external_player_missing"} & issue_codes
        )

        video_bridge_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-video-bridge",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(video_bridge_description.returncode, 0, video_bridge_description.stdout + video_bridge_description.stderr)
        video_bridge_payload = json.loads(video_bridge_description.stdout)
        self.assertEqual(video_bridge_payload["summary"]["videoAssetCount"], 1)
        self.assertEqual(video_bridge_payload["summary"]["videoBlockCount"], 1)
        self.assertEqual(video_bridge_payload["entries"][0]["externalPlaybackMode"], "system_player_bridge")
        self.assertEqual(video_bridge_payload["entries"][0]["nativePreviewMode"], "cinematic_bridge_card")
        self.assertTrue(video_bridge_payload["entries"][0]["exists"])
        self.assertTrue(video_bridge_payload["entries"][0]["extensionSupported"])
        self.assertEqual(video_bridge_payload["entries"][0]["usages"][0]["title"], "Opening Movie")

    def test_voice_placeholder_and_match_workflow(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这句台词会生成语音占位。",
                }
            ],
        )

        placeholder_result = run_editor.create_voice_placeholder(
            chapter_result["sceneId"],
            "block_001",
        )

        self.assertFalse(placeholder_result["alreadyBound"])
        self.assertEqual(placeholder_result["asset"]["type"], "voice")

        asset_name = placeholder_result["asset"]["name"]
        match_result = run_editor.match_voice_files_to_placeholders(
            [build_upload_payload(f"{asset_name}.wav", build_fake_wav_bytes())],
            [placeholder_result["assetId"]],
        )

        self.assertEqual(match_result["matchedCount"], 1)
        matched_asset = match_result["assets"][0]
        self.assertTrue((run_editor.TEMPLATE_DIR / matched_asset["path"]).is_file())

        bundle = run_editor.load_project_bundle()
        saved_block = bundle["chapters"][0]["scenes"][0]["blocks"][0]
        self.assertEqual(saved_block["voiceAssetId"], placeholder_result["assetId"])

    def test_legacy_project_auto_migrates_when_opened(self) -> None:
        legacy_dir = self.projects_dir / "legacy_story"
        chapters_dir = legacy_dir / "data" / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        run_editor.write_json(
            legacy_dir / "project.json",
            {
                "title": "旧项目",
                "template": "legacy_template",
                "resolution": {"width": 1280, "height": 720},
                "chapterOrder": ["missing_chapter", "chapter_opening"],
                "createdAt": "2026-04-01T10:00:00+08:00",
            },
        )
        run_editor.write_json(
            legacy_dir / "data" / "assets.json",
            [
                {
                    "type": "background",
                    "name": "旧背景",
                    "path": "assets/backgrounds/legacy_bg.png",
                }
            ],
        )
        run_editor.write_json(
            legacy_dir / "data" / "characters.json",
            [
                {
                    "displayName": "旧角色",
                    "defaultPosition": "unknown",
                    "expressions": [
                        {
                            "name": "默认",
                            "spriteAssetId": "sprite_legacy_default",
                        }
                    ],
                }
            ],
        )
        run_editor.write_json(
            chapters_dir / "chapter_01.json",
            {
                "chapterId": "chapter_opening",
                "name": "旧章节",
                "scenes": [
                    {
                        "name": "旧开场",
                        "blocks": [
                            {
                                "type": "dialogue",
                                "text": "这是旧格式里的第一句。",
                            }
                        ],
                    },
                    {
                        "id": "scene_ready",
                        "blocks": "not-a-list",
                    },
                ],
            },
        )

        summary = run_editor.activate_project("legacy_story")
        bundle = run_editor.load_project_bundle()

        self.assertEqual(summary["projectId"], "legacy_story")
        self.assertEqual(bundle["project"]["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(bundle["project"]["projectId"], "legacy_story")
        self.assertEqual(bundle["project"]["releaseVersion"], run_editor.DEFAULT_EXPORT_RELEASE_VERSION)
        self.assertEqual(bundle["project"]["editorMode"], run_editor.DEFAULT_EDITOR_MODE)
        self.assertEqual(bundle["project"]["chapterOrder"], ["chapter_opening"])
        self.assertTrue(bundle["project"]["entrySceneId"])

        assets_doc = run_editor.read_json(legacy_dir / "data" / "assets.json")
        self.assertEqual(assets_doc["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(len(assets_doc["assets"]), 1)
        self.assertTrue(assets_doc["assets"][0]["id"].startswith("bg_"))
        self.assertEqual(assets_doc["assets"][0]["tags"], [])

        characters_doc = run_editor.read_json(legacy_dir / "data" / "characters.json")
        self.assertEqual(characters_doc["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(len(characters_doc["characters"]), 1)
        self.assertTrue(characters_doc["characters"][0]["id"].startswith("char_"))
        self.assertEqual(characters_doc["characters"][0]["defaultPosition"], "center")
        self.assertTrue(characters_doc["characters"][0]["expressions"][0]["id"].startswith("expr_"))

        variables_doc = run_editor.read_json(legacy_dir / "data" / "variables.json")
        self.assertEqual(variables_doc["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(variables_doc["variables"], [])

        chapter_doc = run_editor.read_json(chapters_dir / "chapter_01.json")
        self.assertEqual(chapter_doc["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(chapter_doc["sceneOrder"], [scene["id"] for scene in chapter_doc["scenes"]])
        self.assertEqual(chapter_doc["scenes"][0]["status"], "drafting")
        self.assertEqual(chapter_doc["scenes"][0]["priority"], "normal")
        self.assertEqual(chapter_doc["scenes"][0]["blocks"][0]["id"], "block_001")
        self.assertEqual(chapter_doc["scenes"][1]["blocks"], [])

        history = run_editor.build_history_payload(legacy_dir)
        self.assertGreaterEqual(history["totalSnapshots"], 2)
        self.assertEqual(history["currentSnapshot"]["kind"], "migration")

    def test_web_export_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是网页导出烟测。",
                }
            ],
        )

        export_result = run_editor.export_web_build()

        build_dir = Path(export_result["buildPath"])
        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_WEB)
        self.assertTrue((build_dir / "index.html").is_file())
        self.assertTrue((build_dir / "player.js").is_file())
        self.assertTrue((build_dir / "player.css").is_file())
        self.assertTrue((build_dir / "launch_splash.svg").is_file())
        self.assertTrue((build_dir / "app_icon.png").is_file())
        self.assertTrue((build_dir / "app_icon.ico").is_file())
        self.assertTrue(manifest_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_WEB)
        self.assertEqual(
            manifest["engine"]["releaseVersion"],
            run_editor.DEFAULT_EXPORT_RELEASE_VERSION,
        )

    def test_native_runtime_export_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        ui_assets = run_editor.import_assets(
            "ui",
            [
                build_upload_payload("title_background.png", build_fake_png_bytes()),
                build_upload_payload("title_logo.png", build_fake_png_bytes()),
                build_upload_payload("panel_frame.png", build_fake_png_bytes()),
                build_upload_payload("button_frame.png", build_fake_png_bytes()),
                build_upload_payload("button_hover_frame.png", build_fake_png_bytes()),
                build_upload_payload("button_pressed_frame.png", build_fake_png_bytes()),
                build_upload_payload("button_disabled_frame.png", build_fake_png_bytes()),
                build_upload_payload("save_slot_frame.png", build_fake_png_bytes()),
                build_upload_payload("system_panel_frame.png", build_fake_png_bytes()),
                build_upload_payload("ui_overlay.png", build_fake_png_bytes()),
            ],
        )["assets"]
        run_editor.save_project_settings(
            runtime_settings={"formalSaveSlotCount": 60},
            game_ui_config={
                "preset": "paper",
                "layoutPreset": "compact",
                "titleLayout": "left",
                "fontStyle": "serif",
                "surfaceStyle": "solid",
                "brandMode": "project",
                "sidePanelMode": "compact",
                "sidePanelPosition": "left",
                "topbarPosition": "top",
                "hudPosition": "bottom-left",
                "titleCardAnchor": "left",
                "titleCardOffsetXPercent": 3,
                "titleCardOffsetYPercent": 2,
                "layoutGap": 16,
                "sidePanelWidth": 280,
                "titleBackgroundAssetId": ui_assets[0]["id"],
                "titleLogoAssetId": ui_assets[1]["id"],
                "titleBackgroundFit": "contain",
                "titleBackgroundOpacity": 33,
                "panelFrameAssetId": ui_assets[2]["id"],
                "panelFrameSlice": {"top": 9, "right": 11, "bottom": 13, "left": 15},
                "buttonFrameAssetId": ui_assets[3]["id"],
                "buttonHoverFrameAssetId": ui_assets[4]["id"],
                "buttonPressedFrameAssetId": ui_assets[5]["id"],
                "buttonDisabledFrameAssetId": ui_assets[6]["id"],
                "panelFrameOpacity": 22,
                "buttonFrameOpacity": 12,
                "buttonFrameSlice": {"top": 7, "right": 12, "bottom": 7, "left": 12},
                "saveSlotFrameAssetId": ui_assets[7]["id"],
                "systemPanelFrameAssetId": ui_assets[8]["id"],
                "uiOverlayAssetId": ui_assets[9]["id"],
                "uiOverlayOpacity": 5,
            },
        )

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {"id": "block_001", "type": "background", "assetId": ""},
                {
                    "id": "block_001b",
                    "type": "particle_effect",
                    "action": "start",
                    "preset": "snow",
                    "intensity": "medium",
                    "speed": "medium",
                    "wind": "still",
                    "area": "full",
                },
                {"id": "block_001c", "type": "screen_flash", "color": "white", "intensity": "soft", "duration": "short"},
                {"id": "block_001d", "type": "camera_zoom", "action": "zoom_in", "strength": "light", "focus": "center"},
                {"id": "block_001e", "type": "screen_filter", "action": "apply", "preset": "memory", "strength": "soft"},
                {
                    "id": "block_002",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是原生 Runtime 包烟测。",
                },
            ],
        )

        export_result = run_editor.export_native_runtime_build()

        build_dir = Path(export_result["buildPath"])
        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_NATIVE_RUNTIME)
        self.assertTrue((build_dir / "game_data.json").is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_README_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_REQUIREMENTS_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_BUILD_REQUIREMENTS_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_APP_BUILDER_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_BRAND_LOGO_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_MAC_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_LINUX_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_WINDOWS_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_MAC_APP_BUILDER_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_LINUX_APP_BUILDER_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_WINDOWS_APP_BUILDER_COMMAND_NAME).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue(manifest_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_NATIVE_RUNTIME)
        self.assertEqual(manifest["runtime"]["mode"], "pygame_native")
        self.assertTrue(manifest["runtime"]["canBuildStandaloneApp"])

        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        self.assertEqual(release_check_payload["status"], "pass")
        self.assertEqual(release_check_payload["summary"]["errors"], 0)

        game_data = json.loads((build_dir / "game_data.json").read_text(encoding="utf-8"))
        self.assertIn("gameUiConfig", game_data["project"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["preset"], "paper")
        self.assertEqual(game_data["project"]["gameUiConfig"]["layoutPreset"], "compact")
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleLayout"], "left")
        self.assertEqual(game_data["project"]["gameUiConfig"]["sidePanelPosition"], "left")
        self.assertEqual(game_data["project"]["gameUiConfig"]["hudPosition"], "bottom-left")
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleCardAnchor"], "left")
        self.assertEqual(game_data["project"]["gameUiConfig"]["sidePanelWidth"], 280)
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleBackgroundAssetId"], ui_assets[0]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleLogoAssetId"], ui_assets[1]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleBackgroundFit"], "contain")
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleBackgroundOpacity"], 33)
        self.assertEqual(game_data["project"]["gameUiConfig"]["panelFrameAssetId"], ui_assets[2]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["panelFrameSlice"], {"top": 9, "right": 11, "bottom": 13, "left": 15})
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonFrameAssetId"], ui_assets[3]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonHoverFrameAssetId"], ui_assets[4]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonPressedFrameAssetId"], ui_assets[5]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonDisabledFrameAssetId"], ui_assets[6]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonFrameSlice"], {"top": 7, "right": 12, "bottom": 7, "left": 12})
        self.assertEqual(game_data["project"]["gameUiConfig"]["saveSlotFrameAssetId"], ui_assets[7]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["systemPanelFrameAssetId"], ui_assets[8]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["uiOverlayAssetId"], ui_assets[9]["id"])

        app_builder_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_APP_BUILDER_NAME),
                "--describe",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(app_builder_description.returncode, 0, app_builder_description.stdout + app_builder_description.stderr)
        app_builder_payload = json.loads(app_builder_description.stdout)
        self.assertEqual(app_builder_payload["gameData"], "game_data.json")
        self.assertEqual(app_builder_payload["runtimePlayer"], run_editor.NATIVE_RUNTIME_PLAYER_NAME)
        self.assertEqual(app_builder_payload["outputDir"], "native_app_dist")
        self.assertEqual(app_builder_payload["packageManifest"], "native_app_package_manifest.json")
        self.assertTrue(app_builder_payload["plannedArchiveName"].endswith("-preview.zip"))
        self.assertIn(app_builder_payload["platform"], {"macos", "windows", "linux", "unknown"})
        self.assertTrue(app_builder_payload["bundleIdentifier"].startswith("com.tonyna."))
        self.assertTrue(app_builder_payload["distributionNotes"])
        self.assertTrue(app_builder_payload["dataEntries"])
        self.assertFalse(app_builder_payload["missingAssetPaths"])
        self.assertEqual(app_builder_payload["releaseCheck"]["status"], "pass")
        self.assertTrue(
            any(entry["source"] == run_editor.NATIVE_RUNTIME_BRAND_LOGO_NAME for entry in app_builder_payload["dataEntries"])
        )

        title_screen_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-title-screen",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(title_screen_description.returncode, 0, title_screen_description.stdout + title_screen_description.stderr)
        title_screen_payload = json.loads(title_screen_description.stdout)
        self.assertEqual(title_screen_payload["status"], "ready")
        self.assertTrue(title_screen_payload["engineBrandLogoExists"])
        self.assertIn("start", {item["key"] for item in title_screen_payload["menuItems"]})
        self.assertIn("settings", {item["key"] for item in title_screen_payload["menuItems"]})

        validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--validate-bundle",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

        save_load_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-save-load",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(save_load_validation.returncode, 0, save_load_validation.stdout + save_load_validation.stderr)

        settings_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-settings",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(settings_validation.returncode, 0, settings_validation.stdout + settings_validation.stderr)

        archive_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-archives",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(archive_validation.returncode, 0, archive_validation.stdout + archive_validation.stderr)

        particle_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-particles",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(particle_validation.returncode, 0, particle_validation.stdout + particle_validation.stderr)

        visual_effect_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-visual-effects",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(visual_effect_validation.returncode, 0, visual_effect_validation.stdout + visual_effect_validation.stderr)

        profile_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-profile",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(profile_validation.returncode, 0, profile_validation.stdout + profile_validation.stderr)

        save_dialog_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-save-dialog",
                str(build_dir),
                "--page",
                "1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(save_dialog_description.returncode, 0, save_dialog_description.stdout + save_dialog_description.stderr)
        dialog_payload = json.loads(save_dialog_description.stdout)
        self.assertEqual(dialog_payload["slotCount"], 60)
        self.assertEqual(dialog_payload["pageCount"], 10)
        self.assertEqual(dialog_payload["page"], 1)
        self.assertEqual(dialog_payload["visibleSlots"][0]["slotIndex"], 6)

    def test_macos_nwjs_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是 macOS 桌面导出烟测。",
                }
            ],
        )

        export_result = run_editor.export_macos_nwjs_build()

        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_MACOS_NWJS)
        self.assertTrue(Path(export_result["appBundlePath"]).is_dir())
        self.assertTrue(Path(export_result["startHelperPath"]).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue(manifest_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_MACOS_NWJS)
        self.assertEqual(manifest["runtime"]["version"], run_editor.NWJS_RUNTIME_VERSION)

    def test_linux_nwjs_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是 Linux 桌面导出烟测。",
                }
            ],
        )

        export_result = run_editor.export_linux_nwjs_build()

        build_dir = Path(export_result["buildPath"])
        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_LINUX_NWJS)
        self.assertTrue(Path(export_result["launcherPath"]).is_file())
        self.assertTrue(Path(export_result["startHelperPath"]).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue((build_dir / "package.nw").is_file())
        self.assertTrue(manifest_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_LINUX_NWJS)
        self.assertEqual(manifest["runtime"]["version"], run_editor.NWJS_RUNTIME_VERSION)

    def test_editor_desktop_build_smoke(self) -> None:
        export_result = run_editor.export_editor_desktop_build()

        build_dir = Path(export_result["buildPath"])
        bundle_dir = Path(export_result["bundleDirPath"])
        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_EDITOR_DESKTOP)
        self.assertTrue(bundle_dir.is_dir())
        self.assertTrue((bundle_dir / "run_editor.py").is_file())
        self.assertTrue((bundle_dir / "prototype_editor" / "index.html").is_file())
        self.assertTrue((bundle_dir / "export_player_template" / "player.js").is_file())
        self.assertTrue((bundle_dir / "template_project" / "project.json").is_file())
        self.assertTrue((bundle_dir / "projects").is_dir())
        self.assertTrue((bundle_dir / "exports").is_dir())
        self.assertTrue((build_dir / run_editor.EDITOR_START_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_START_WINDOWS_NAME).is_file())
        self.assertTrue((build_dir / "launch_splash.svg").is_file())
        self.assertTrue((build_dir / "app_icon.png").is_file())
        self.assertTrue((build_dir / "app_icon.ico").is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_DISTRIBUTION_SNAPSHOT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_COMMERCIAL_README_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_GUIDE_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_ENV_EXAMPLE_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_CHECK_SCRIPT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_CHECK_COMMAND_NAME).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue(manifest_path.is_file())
        self.assertTrue(Path(export_result["signingGuidePath"]).is_file())
        self.assertTrue(Path(export_result["signingEnvExamplePath"]).is_file())
        self.assertTrue(Path(export_result["signingCheckScriptPath"]).is_file())
        self.assertTrue(Path(export_result["signingCheckCommandPath"]).is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["packageTarget"], run_editor.EXPORT_TARGET_EDITOR_DESKTOP)
        self.assertEqual(manifest["engine"]["releaseVersion"], run_editor.EDITOR_PACKAGE_VERSION)
        self.assertEqual(manifest["editorPackage"]["bundleDirName"], run_editor.EDITOR_BUNDLE_DIR_NAME)
        self.assertIn("embeddedRuntime", manifest["editorPackage"])
        self.assertIn("commercialRelease", manifest["editorPackage"])
        self.assertIn(export_result["embeddedRuntimeMode"], {run_editor.EDITOR_RUNTIME_SOURCE_CONDA_PACK, run_editor.EDITOR_RUNTIME_SOURCE_SYSTEM})
        if export_result["embeddedRuntimeIncluded"]:
            self.assertTrue((bundle_dir / run_editor.EDITOR_RUNTIME_DIR_NAME / "bin" / "python3").is_file())

        if run_editor.should_build_editor_macos_app():
            self.assertTrue((build_dir / run_editor.EDITOR_MAC_APP_NAME).is_dir())
            self.assertTrue((build_dir / run_editor.EDITOR_MAC_APP_NAME / "Contents" / "Resources" / run_editor.EDITOR_BUNDLE_DIR_NAME / "run_editor.py").is_file())
            self.assertTrue((build_dir / run_editor.EDITOR_MAC_INSTALLER_NAME).is_file())

    def test_editor_desktop_suite_build_smoke(self) -> None:
        export_result = run_editor.export_editor_desktop_suite_build()
        build_dir = Path(export_result["buildPath"])
        manifest_path = Path(export_result["manifestPath"])

        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_EDITOR_DESKTOP_SUITE)
        self.assertTrue(manifest_path.is_file())
        self.assertTrue((build_dir / "README_三系统编辑器套装先看这里.txt").is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_DISTRIBUTION_SNAPSHOT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_GUIDE_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_ENV_EXAMPLE_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_CHECK_SCRIPT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_CHECK_COMMAND_NAME).is_file())
        self.assertEqual(len(export_result["packages"]), 3)
        self.assertTrue(Path(export_result["signingGuidePath"]).is_file())
        self.assertTrue(Path(export_result["signingEnvExamplePath"]).is_file())
        self.assertTrue(Path(export_result["signingCheckScriptPath"]).is_file())
        self.assertTrue(Path(export_result["signingCheckCommandPath"]).is_file())

        platform_map = {package["platform"]: package for package in export_result["packages"]}
        self.assertIn(run_editor.EDITOR_PLATFORM_MACOS, platform_map)
        self.assertIn(run_editor.EDITOR_PLATFORM_WINDOWS, platform_map)
        self.assertIn(run_editor.EDITOR_PLATFORM_LINUX, platform_map)

        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_MACOS]["archivePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["archivePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["archivePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["runtimeInfo"]["runtimeDirPath"]).is_dir())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["runtimeInfo"]["runtimeDirPath"]).is_dir())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_MACOS]["runtimeInfo"]["runtimeDirPath"]).is_dir())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["commercialReadmePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingGuidePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingEnvExamplePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingCheckScriptPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingCheckCommandPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsInstallerScriptPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsInstallerExePath"]).is_file())
        self.assertEqual(
            platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsInstallerCompileStatusLabel"],
            "已编译 Windows 安装器",
        )
        self.assertEqual(
            platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsSigningStatusLabel"],
            "已签名并加时间戳",
        )
        self.assertTrue(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsInstallerSigned"])
        self.assertEqual(
            platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingInfo"]["statusLabel"],
            "已签名并加时间戳",
        )
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["commercialReadmePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["signingGuidePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["signingEnvExamplePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["signingCheckScriptPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["signingCheckCommandPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["linuxInstallScriptPath"]).is_file())

        if run_editor.should_build_editor_macos_app():
            self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_MACOS]["appPath"]).is_dir())
            self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_MACOS]["installerPath"]).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
