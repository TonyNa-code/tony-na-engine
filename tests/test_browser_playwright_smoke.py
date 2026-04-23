from __future__ import annotations

import shutil
import socket
import subprocess
import sys
import tempfile
import time
import os
import tarfile
import unittest
import re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def wait_for_server_ready(url: str, process: subprocess.Popen[str], timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"测试服务提前退出。\n{output}")
        try:
            with urlopen(url, timeout=1.5) as response:
                if 200 <= getattr(response, "status", 200) < 500:
                    return
        except Exception as error:  # pragma: no cover - readiness polling
            last_error = str(error)
            time.sleep(0.25)
    raise RuntimeError(f"测试服务没有在规定时间内启动：{last_error}")


def create_fake_runtime_archive(archive_path: Path, platform_key: str) -> Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "python"
        if platform_key == "windows":
            executable = root / "python.exe"
        else:
            executable = root / "bin" / "python3"
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("fake-python", encoding="utf-8")
        if platform_key != "windows":
            executable.chmod(0o755)
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(root, arcname="python")
    return archive_path


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


class BrowserPlaywrightSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.repo_source = Path("/Users/na/Game Engine")
        cls.repo_copy = Path(cls.temp_dir.name) / "browser_test_repo"
        shutil.copytree(
            cls.repo_source,
            cls.repo_copy,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                ".DS_Store",
                "exports",
                ".export_runtime_cache",
                ".tmp_brand_preview",
                "projects",
            ),
        )
        cls.fake_runtime_archives = {
            "macos": create_fake_runtime_archive(cls.repo_copy / ".tmp_fake_macos_runtime.tar.gz", "macos"),
            "windows": create_fake_runtime_archive(cls.repo_copy / ".tmp_fake_windows_runtime.tar.gz", "windows"),
            "linux": create_fake_runtime_archive(cls.repo_copy / ".tmp_fake_linux_runtime.tar.gz", "linux"),
        }
        cls.fake_iscc = create_fake_iscc_script(cls.repo_copy / ".tmp_fake_iscc.sh")
        cls.fake_signtool = create_fake_signtool_script(cls.repo_copy / ".tmp_fake_signtool.sh")

        cls.port = find_free_port()
        cls.editor_url = f"http://127.0.0.1:{cls.port}/prototype_editor/index.html"
        server_env = os.environ.copy()
        server_env.update(
            {
                "TONY_NA_EDITOR_RUNTIME_ARCHIVE_MACOS": str(cls.fake_runtime_archives["macos"]),
                "TONY_NA_EDITOR_RUNTIME_ARCHIVE_WINDOWS": str(cls.fake_runtime_archives["windows"]),
                "TONY_NA_EDITOR_RUNTIME_ARCHIVE_LINUX": str(cls.fake_runtime_archives["linux"]),
                "TONY_NA_EDITOR_WINDOWS_ISCC": str(cls.fake_iscc),
                "TONY_NA_EDITOR_WINDOWS_SIGNTOOL": str(cls.fake_signtool),
                "TONY_NA_EDITOR_WINDOWS_CERT_SUBJECT": "Tony Na Studio",
            }
        )
        cls.server_process = subprocess.Popen(
            [sys.executable, str(cls.repo_copy / "run_editor.py"), "--port", str(cls.port), "--no-open"],
            cwd=cls.repo_copy,
            env=server_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        wait_for_server_ready(cls.editor_url, cls.server_process)

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.browser.close()
        except Exception:
            pass
        try:
            cls.playwright.stop()
        except Exception:
            pass
        try:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
        except Exception:
            try:
                cls.server_process.kill()
            except Exception:
                pass
        try:
            if cls.server_process.stdout:
                cls.server_process.stdout.close()
        except Exception:
            pass
        cls.temp_dir.cleanup()

    def setUp(self) -> None:
        self.context = self.browser.new_context(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        self.page = self.context.new_page()

    def tearDown(self) -> None:
        self.context.close()

    def open_editor(self) -> None:
        self.page.goto(self.editor_url, wait_until="domcontentloaded")
        self.page.get_by_text("先选项目，再进入编辑器").wait_for(timeout=15000)

    def create_blank_project(self, name: str) -> None:
        self.open_editor()
        self.page.once("dialog", lambda dialog: dialog.accept(name))
        self.page.get_by_role("button", name="新建空白项目").click()
        self.page.get_by_role("button", name="一键创建第一章").first.wait_for(timeout=15000)

    def create_first_chapter(self) -> None:
        self.page.get_by_role("button", name="一键创建第一章").first.click()
        self.page.locator("#screen-story").get_by_role("button", name="加台词").first.wait_for(timeout=15000)

    def open_project_by_title(self, title: str) -> None:
        self.open_editor()
        card = self.page.locator(".project-card").filter(has_text=title).first
        card.wait_for(timeout=15000)
        card.locator("[data-action='open-project']").click()
        self.page.get_by_role("button", name="试玩收尾").wait_for(timeout=15000)

    def open_inspection_screen(self) -> None:
        inspection_button = self.page.get_by_role("button", name="项目巡检").first
        if not inspection_button.is_visible():
            advanced_button = self.page.get_by_role("button", name="打开高级工具").first
            advanced_button.wait_for(timeout=10000)
            advanced_button.click()
            inspection_button.wait_for(timeout=10000)
        inspection_button.click()
        self.page.get_by_role("heading", name="一键巡检中心").wait_for(timeout=15000)

    def open_preview_screen(self) -> None:
        self.page.get_by_role("button", name="试玩收尾").click()
        self.page.get_by_text("新手收尾顺序").wait_for(timeout=15000)

    def export_web_build(self) -> str:
        self.open_preview_screen()
        self.page.get_by_role("button", name="导出试玩包").first.click()
        open_link = self.page.get_by_role("link", name="打开试玩包")
        open_link.wait_for(timeout=20000)
        href = open_link.get_attribute("href")
        self.assertTrue(href, "导出试玩包后没有拿到可打开链接")
        return urljoin(self.editor_url, href)

    def unlock_sample_player_title_features(
        self,
        player_page,
        *,
        include_voice_replay: bool = False,
        include_endings: bool = False,
        include_gallery: bool = False,
    ) -> None:
        player_page.locator("#startOverlay").wait_for(state="visible", timeout=20000)
        player_page.evaluate(
            """(options) => {
                const now = new Date().toISOString();
                window.localStorage.setItem(
                    "tony-na-engine:player-chapters:心跳时差",
                    JSON.stringify({ chapter_opening: now })
                );
                window.localStorage.setItem(
                    "tony-na-engine:player-extra:心跳时差",
                    JSON.stringify({
                        cg: options?.includeGallery ? ["cg_twilight_memory"] : [],
                        bgm: ["bgm_after_school"],
                    })
                );
                if (options?.includeVoiceReplay) {
                    window.localStorage.setItem(
                        "tony-na-engine:player-voice-replay:心跳时差",
                        JSON.stringify({
                            "scene_classroom_sunset:block_005:6": {
                                unlockedAt: now,
                                lastHeardAt: now,
                                heardCount: 1,
                            },
                            "scene_classroom_sunset:block_006:7": {
                                unlockedAt: now,
                                lastHeardAt: now,
                                heardCount: 1,
                            },
                            "scene_classroom_sunset:block_007:8": {
                                unlockedAt: now,
                                lastHeardAt: now,
                                heardCount: 1,
                            },
                        })
                    );
                }

                if (options?.includeEndings) {
                    window.localStorage.setItem(
                        "tony-na-engine:player-endings:心跳时差",
                        JSON.stringify({
                            unlocked: {
                                scene_normal_goodnight: now,
                            },
                            completionCount: 1,
                            lastCompletedAt: now,
                        })
                    );
                }
            }""",
            {
                "includeVoiceReplay": include_voice_replay,
                "includeEndings": include_endings,
                "includeGallery": include_gallery,
            },
        )
        player_page.reload(wait_until="domcontentloaded")
        player_page.locator("#startOverlay").wait_for(state="visible", timeout=15000)
        player_page.wait_for_function(
            """(options) => {
                const chapterText = document.querySelector("#startChapterButton")?.textContent || "";
                const musicText = document.querySelector("#startMusicRoomButton")?.textContent || "";
                const voiceText = document.querySelector("#startVoiceReplayButton")?.textContent || "";
                const endingText = document.querySelector("#startEndingButton")?.textContent || "";
                const galleryText = document.querySelector("#startGalleryButton")?.textContent || "";

                if (!chapterText.includes("1/1") || !musicText.includes("1/1")) {
                    return false;
                }

                if (options?.includeVoiceReplay && !voiceText.includes("3/3")) {
                    return false;
                }

                if (options?.includeEndings && !endingText.includes("1/2")) {
                    return false;
                }

                if (options?.includeGallery && !galleryText.includes("1/1")) {
                    return false;
                }

                return true;
            }""",
            arg={
                "includeVoiceReplay": include_voice_replay,
                "includeEndings": include_endings,
                "includeGallery": include_gallery,
            },
            timeout=10000,
        )

    def unlock_sample_player_collection_archives(self, player_page) -> None:
        player_page.locator("#startOverlay").wait_for(state="visible", timeout=20000)
        player_page.evaluate(
            """() => {
                const now = new Date().toISOString();
                window.localStorage.setItem(
                    "tony-na-engine:player-locations:心跳时差",
                    JSON.stringify({
                        bg_classroom_sunset: now,
                        bg_hallway_after_school: now,
                        bg_rooftop_evening: now,
                    })
                );
                window.localStorage.setItem(
                    "tony-na-engine:player-narrations:心跳时差",
                    JSON.stringify({
                        "scene_rooftop_breeze:block_014:1": now,
                        "scene_normal_goodnight:block_023:1": now,
                    })
                );
                window.localStorage.setItem(
                    "tony-na-engine:player-relations:心跳时差",
                    JSON.stringify({
                        "char_linruoxi__char_player": now,
                    })
                );
                window.localStorage.setItem(
                    "tony-na-engine:player-characters:心跳时差",
                    JSON.stringify(["char_linruoxi", "char_player"])
                );
            }"""
        )
        player_page.reload(wait_until="domcontentloaded")
        player_page.locator("#startOverlay").wait_for(state="visible", timeout=15000)
        player_page.wait_for_function(
            """() => {
                const locationText = document.querySelector("#startLocationButton")?.textContent || "";
                const narrationText = document.querySelector("#startNarrationButton")?.textContent || "";
                const relationText = document.querySelector("#startRelationButton")?.textContent || "";
                const characterText = document.querySelector("#startCharacterButton")?.textContent || "";
                return locationText.includes("3/3")
                  && narrationText.includes("2/2")
                  && relationText.includes("1/1")
                  && characterText.includes("2/2");
            }""",
            timeout=10000,
        )

    def test_beginner_flow_reaches_story_editor_and_adds_block(self) -> None:
        self.create_blank_project("浏览器烟测项目_A")
        self.create_first_chapter()

        block_cards = self.page.locator("#storyBlockList .block-card")
        initial_count = block_cards.count()
        self.page.locator("#screen-story").get_by_role("button", name="加台词").first.click()
        self.page.wait_for_function(
            """([selector, expected]) => {
                const cards = document.querySelectorAll(selector);
                return cards.length > expected;
            }""",
            arg=["#storyBlockList .block-card", initial_count],
            timeout=15000,
        )

        self.assertGreater(block_cards.count(), initial_count)

    def test_beginner_flow_can_export_web_build(self) -> None:
        self.create_blank_project("浏览器烟测项目_B")
        self.create_first_chapter()

        player_url = self.export_web_build()
        self.assertIn("/exports/", player_url)

    def test_inspection_flow_can_run_regression_and_export_report(self) -> None:
        self.create_blank_project("浏览器烟测项目_C")
        self.create_first_chapter()
        self.open_inspection_screen()

        self.page.get_by_role("button", name="自动回归试玩路线测试").first.click()
        self.page.get_by_text("已测试路线").wait_for(timeout=15000)

        with self.page.expect_download() as download_info:
            self.page.get_by_role("button", name="导出巡检报告").first.click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))

        self.assertTrue(download_path.exists())
        report_content = download_path.read_text(encoding="utf-8-sig")
        self.assertIn("项目巡检报告", report_content)
        self.assertIn("自动回归试玩路线测试", report_content)

    def test_preview_flow_can_export_windows_build(self) -> None:
        self.create_blank_project("浏览器烟测项目_D")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_role("button", name="导出 Windows 桌面包").click()
        download_link = self.page.get_by_role("link", name="下载桌面包压缩档")
        download_link.wait_for(timeout=60000)

        with self.page.expect_download() as download_info:
            download_link.click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))

        self.assertTrue(download_path.exists())
        self.assertGreater(download_path.stat().st_size, 0)

    def test_preview_flow_can_export_editor_desktop_build(self) -> None:
        self.create_blank_project("浏览器烟测项目_Editor")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_role("button", name="导出编辑器桌面包").click()
        download_link = self.page.get_by_role("link", name="下载编辑器包压缩档")
        download_link.wait_for(timeout=40000)
        self.page.get_by_text("编辑器包目录：").wait_for(timeout=10000)
        if sys.platform == "darwin":
            self.page.get_by_role("link", name="下载 mac 安装包").wait_for(timeout=10000)
            self.page.get_by_text("mac 安装包：").wait_for(timeout=10000)

        with self.page.expect_download() as download_info:
            download_link.click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))

        self.assertTrue(download_path.exists())
        self.assertGreater(download_path.stat().st_size, 0)

    def test_preview_flow_can_export_editor_desktop_suite(self) -> None:
        self.create_blank_project("浏览器烟测项目_EditorSuite")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_role("button", name="导出三系统编辑器套装").click()
        self.page.get_by_role("link", name="打开三系统套装清单").wait_for(timeout=40000)
        self.page.get_by_text("已生成 3 组平台包").wait_for(timeout=15000)
        self.page.get_by_text("macOS：").wait_for(timeout=10000)
        self.page.get_by_text("Windows：").wait_for(timeout=10000)
        self.page.get_by_text("Linux：").wait_for(timeout=10000)
        self.page.get_by_text("安装器：已编译 Windows 安装器").wait_for(timeout=10000)
        self.page.get_by_text("已签名并加时间戳").wait_for(timeout=10000)
        self.page.get_by_role("link", name="打开签名操作手册").wait_for(timeout=10000)
        self.page.get_by_role("link", name="打开签名配置模板").wait_for(timeout=10000)
        self.page.get_by_role("link", name="打开签名前自检脚本").wait_for(timeout=10000)

    def test_exported_player_can_formal_save_and_load(self) -> None:
        self.create_blank_project("浏览器烟测项目_E")
        self.create_first_chapter()
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            player_page.locator("#startButton").wait_for(timeout=20000)
            player_page.locator("#startButton").click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)

            player_page.locator("#systemMenuButton").click()
            player_page.locator("#systemMenu").wait_for(state="visible", timeout=10000)
            player_page.locator("#systemMenuOpenSaveButton").click()
            player_page.locator("#saveDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#saveDialog [data-save-slot='1']").click()
            player_page.wait_for_function(
                """() => {
                    const clearButton = document.querySelector("#saveDialog [data-clear-slot='1']");
                    return Boolean(clearButton) && !clearButton.disabled;
                }""",
                timeout=15000,
            )

            player_page.locator("#closeSaveDialogButton").click()
            player_page.locator("#saveDialog").wait_for(state="hidden", timeout=10000)

            player_page.locator("#systemMenuButton").click()
            player_page.locator("#systemMenuReturnTitleButton").click()
            player_page.locator("#returnTitleDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#confirmReturnTitleButton").click()
            player_page.locator("#startOverlay").wait_for(state="visible", timeout=15000)

            player_page.locator("#startLoadButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startLoadButton").click()
            player_page.locator("#saveDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#saveDialog [data-load-slot='1']").wait_for(timeout=10000)
            player_page.locator("#saveDialog [data-load-slot='1']").click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)
        finally:
            player_page.close()

    def test_exported_player_sample_project_can_open_archive_dialogs(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page)
            player_page.locator("#startVoiceReplayButton").wait_for(state="visible", timeout=10000)

            archive_buttons = [
                ("#startProfileButton", "#profileDialog", "#closeProfileDialogButton"),
                ("#startAchievementButton", "#achievementDialog", "#closeAchievementDialogButton"),
                ("#startChapterButton", "#chapterDialog", "#closeChapterDialogButton"),
                ("#startLocationButton", "#locationDialog", "#closeLocationDialogButton"),
                ("#startNarrationButton", "#narrationDialog", "#closeNarrationDialogButton"),
                ("#startRelationButton", "#relationDialog", "#closeRelationDialogButton"),
                ("#startCharacterButton", "#characterDialog", "#closeCharacterDialogButton"),
                ("#startEndingButton", "#endingDialog", "#closeEndingDialogButton"),
                ("#startGalleryButton", "#galleryDialog", "#closeGalleryDialogButton"),
                ("#startMusicRoomButton", "#musicRoomDialog", "#closeMusicRoomDialogButton"),
            ]

            for button_selector, dialog_selector, close_selector in archive_buttons:
                button = player_page.locator(button_selector)
                button.wait_for(state="visible", timeout=15000)
                button.click()
                player_page.locator(dialog_selector).wait_for(state="visible", timeout=10000)
                player_page.locator(close_selector).click()
                player_page.locator(dialog_selector).wait_for(state="hidden", timeout=10000)

        finally:
            player_page.close()

    def test_exported_player_sample_project_can_replay_chapter_and_open_music_room(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page)

            player_page.locator("#startChapterButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startChapterButton").click()
            player_page.locator("#chapterDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#chapterDialogList [data-chapter-replay]:not([disabled])").first.click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)

            player_page.locator("#systemMenuButton").click()
            player_page.locator("#systemMenu").wait_for(state="visible", timeout=10000)
            player_page.locator("#systemMenuReturnTitleButton").click()
            player_page.locator("#returnTitleDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#confirmReturnTitleButton").click()
            player_page.locator("#startOverlay").wait_for(state="visible", timeout=15000)

            player_page.locator("#startMusicRoomButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startMusicRoomButton").click()
            player_page.locator("#musicRoomDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#musicRoomDialog [data-music-room-play]:not([disabled])").first.click()
            player_page.wait_for_function(
                """() => {
                    const stopButton = document.querySelector("#musicRoomDialog [data-music-room-stop]");
                    const nowPlaying = document.querySelector("#musicRoomNowPlaying")?.textContent || "";
                    return Boolean(stopButton) && nowPlaying.includes("当前试听");
                }""",
                timeout=15000,
            )
            player_page.locator("#musicRoomDialog [data-music-room-stop]").click()
            player_page.locator("#closeMusicRoomDialogButton").click()
            player_page.locator("#musicRoomDialog").wait_for(state="hidden", timeout=10000)
        finally:
            player_page.close()

    def test_exported_player_sample_project_can_replay_unlocked_ending(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_endings=True)

            player_page.locator("#startEndingButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startEndingButton").click()
            player_page.locator("#endingDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#endingDialogList [data-ending-replay]:not([disabled])").first.click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)
            player_page.wait_for_function(
                """() => {
                    const scene = document.querySelector("#sceneChip")?.textContent || "";
                    return scene.includes("普通告别");
                }""",
                timeout=10000,
            )
        finally:
            player_page.close()

    def test_exported_player_sample_project_can_open_gallery_dialog(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_gallery=True)

            player_page.locator("#startGalleryButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startGalleryButton").click()
            player_page.locator("#galleryDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const summary = document.querySelector("#galleryDialogSummary")?.textContent || "";
                    const items = document.querySelectorAll("#galleryDialog [data-gallery-asset-id]");
                    return summary.includes("1 / 1") && items.length === 1;
                }""",
                timeout=10000,
            )
            player_page.locator("#closeGalleryDialogButton").click()
            player_page.locator("#galleryDialog").wait_for(state="hidden", timeout=10000)
        finally:
            player_page.close()

    def test_exported_player_sample_project_can_open_voice_replay_dialog(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_voice_replay=True)

            player_page.locator("#startVoiceReplayButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startVoiceReplayButton").click()
            player_page.locator("#voiceReplayDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const summary = document.querySelector("#voiceReplayDialogSummary")?.textContent || "";
                    const entries = document.querySelectorAll("#voiceReplayDialog [data-voice-replay-id]");
                    return summary.includes("3 / 3") && entries.length === 3;
                }""",
                timeout=10000,
            )
            self.assertGreater(
                player_page.locator("#voiceReplayDialog [data-voice-replay-play]:not([disabled])").count(),
                0,
            )
            player_page.locator("#voiceReplayDialog [data-voice-replay-play]:not([disabled])").first.click()
            player_page.wait_for_timeout(300)
            player_page.locator("#closeVoiceReplayDialogButton").click()
            player_page.locator("#voiceReplayDialog").wait_for(state="hidden", timeout=10000)
        finally:
            player_page.close()

    def test_exported_player_sample_project_archive_dialogs_support_internal_selection(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_gallery=True)
            self.unlock_sample_player_collection_archives(player_page)

            player_page.locator("#startLocationButton").click()
            player_page.locator("#locationDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => document.querySelector("#locationDialogHero strong")?.textContent?.includes("教室黄昏")""",
                timeout=10000,
            )
            player_page.locator("#locationDialog [data-location-archive-id='bg_rooftop_evening']").click()
            player_page.wait_for_function(
                """() => document.querySelector("#locationDialogHero strong")?.textContent?.includes("屋顶晚风")""",
                timeout=10000,
            )
            player_page.locator("#closeLocationDialogButton").click()

            player_page.locator("#startNarrationButton").click()
            player_page.locator("#narrationDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#narrationDialog [data-narration-archive-id='scene_normal_goodnight:block_023:1']").click()
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#narrationDialogHero")?.textContent || "";
                    return hero.includes("今天的故事暂时停在这里");
                }""",
                timeout=10000,
            )
            player_page.locator("#closeNarrationDialogButton").click()

            player_page.locator("#startRelationButton").click()
            player_page.locator("#relationDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#relationDialogHero")?.textContent || "";
                    return hero.includes("林若曦 × 顾言");
                }""",
                timeout=10000,
            )
            player_page.locator("#closeRelationDialogButton").click()

            player_page.locator("#startCharacterButton").click()
            player_page.locator("#characterDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#characterDialog [data-character-archive-id='char_player']").click()
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#characterDialogHero")?.textContent || "";
                    return hero.includes("顾言") && hero.includes("默认站位");
                }""",
                timeout=10000,
            )
            player_page.locator("#closeCharacterDialogButton").click()

            player_page.locator("#startGalleryButton").click()
            player_page.locator("#galleryDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#galleryDialogHero")?.textContent || "";
                    const image = document.querySelector("#galleryDialogHero img");
                    return hero.includes("黄昏回想") && Boolean(image);
                }""",
                timeout=10000,
            )
            player_page.locator("#closeGalleryDialogButton").click()
        finally:
            player_page.close()

    def test_exported_player_sample_project_voice_replay_selection_updates_hero(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_voice_replay=True)

            player_page.locator("#startVoiceReplayButton").click()
            player_page.locator("#voiceReplayDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#voiceReplayDialogHero")?.textContent || "";
                    return hero.includes("林若曦");
                }""",
                timeout=10000,
            )
            player_page.locator("#voiceReplayDialog [data-voice-replay-id='scene_classroom_sunset:block_006:7']").click()
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#voiceReplayDialogHero")?.textContent || "";
                    return hero.includes("顾言") && hero.includes("是吗？我怎么觉得是因为你心情很好");
                }""",
                timeout=10000,
            )
            player_page.locator("#voiceReplayDialog [data-voice-replay-id='scene_classroom_sunset:block_007:8']").click()
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#voiceReplayDialogHero")?.textContent || "";
                    return hero.includes("林若曦") && hero.includes("那你要不要陪我一起走回去");
                }""",
                timeout=10000,
            )
            player_page.locator("#closeVoiceReplayDialogButton").click()
        finally:
            player_page.close()

    def test_exported_player_sample_project_renders_particle_effect_runtime(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            player_page.locator("#startButton").click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)
            player_page.locator("#continueButton").click()
            player_page.wait_for_function(
                """() => {
                    const layer = document.querySelector("#particleLayer .particle-layer");
                    if (!layer) {
                        return false;
                    }
                    const particleCount = layer.querySelectorAll(".particle-item").length;
                    const speaker = document.querySelector("#speakerName")?.textContent || "";
                    return layer.dataset.particlePreset === "snow"
                      && layer.dataset.particleIntensity === "medium"
                      && layer.dataset.particleSpeed === "medium"
                      && layer.dataset.particleArea === "full"
                      && speaker.includes("粒子特效")
                      && particleCount > 0;
                }""",
                timeout=10000,
            )
            player_page.locator("#continueButton").click()
            player_page.wait_for_function(
                """() => Boolean(document.querySelector("#particleLayer .particle-layer"))""",
                timeout=10000,
            )
        finally:
            player_page.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
