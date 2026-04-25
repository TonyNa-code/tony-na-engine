from __future__ import annotations

import json
import os
import tempfile
import unittest
import warnings
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - CI installs pygame-ce for this suite.
    pygame = None

from native_runtime.runtime_player import (
    NativeRuntimePlayer,
    build_native_video_preview_probe_report,
    load_project_archive_progress,
    load_opencv_video_frame_surface,
)


UI_ASSET_IDS = [
    "title_background",
    "title_logo",
    "panel_frame",
    "button_frame",
    "button_hover_frame",
    "button_pressed_frame",
    "button_disabled_frame",
    "save_slot_frame",
    "system_panel_frame",
    "ui_overlay",
]


@unittest.skipIf(pygame is None, "pygame-ce is not installed")
class NativeRuntimeRenderSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_home = os.environ.get("HOME")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        os.environ["HOME"] = str(self.root / "home")
        self.bundle_dir = self.root / "bundle"
        self.bundle_dir.mkdir(parents=True)
        pygame.init()

    def tearDown(self) -> None:
        try:
            pygame.quit()
        finally:
            if self.original_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = self.original_home
            self.temp_dir.cleanup()

    def write_ui_asset(self, asset_id: str, color: tuple[int, int, int, int]) -> dict:
        asset_path = self.bundle_dir / "assets" / "ui" / f"{asset_id}.png"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        pygame.draw.rect(surface, color, surface.get_rect(), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255, 210), surface.get_rect(), width=3, border_radius=6)
        pygame.image.save(surface, str(asset_path))
        return {
            "id": asset_id,
            "type": "ui",
            "name": asset_id.replace("_", " ").title(),
            "exportUrl": asset_path.relative_to(self.bundle_dir).as_posix(),
            "tags": [],
        }

    def write_video_asset(self) -> dict:
        asset_path = self.bundle_dir / "assets" / "video" / "opening.mp4"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_bytes(b"fake-video-data")
        return {
            "id": "opening_video",
            "type": "video",
            "name": "Opening Video",
            "exportUrl": asset_path.relative_to(self.bundle_dir).as_posix(),
            "tags": ["OP"],
        }

    def write_game_data(self) -> Path:
        assets = [
            self.write_ui_asset(asset_id, (70 + index * 11, 92 + index * 7, 180, 235))
            for index, asset_id in enumerate(UI_ASSET_IDS)
        ]
        assets.append(self.write_video_asset())
        game_data = {
            "project": {
                "projectId": "native_render_smoke",
                "title": "Native Render Smoke",
                "entrySceneId": "scene_start",
                "resolution": {"width": 720, "height": 405},
                "runtimeSettings": {"formalSaveSlotCount": 12},
                "dialogBoxConfig": {
                    "preset": "moonlight",
                    "backgroundOpacity": 88,
                    "borderOpacity": 28,
                    "borderWidth": 1,
                },
                "gameUiConfig": {
                    "preset": "custom",
                    "titleBackgroundAssetId": "title_background",
                    "titleLogoAssetId": "title_logo",
                    "fontStyle": "serif",
                    "fontFamily": "Noto Sans CJK SC",
                    "panelFrameAssetId": "panel_frame",
                    "panelFrameOpacity": 68,
                    "panelFrameSlice": {"top": 8, "right": 8, "bottom": 8, "left": 8},
                    "buttonFrameAssetId": "button_frame",
                    "buttonHoverFrameAssetId": "button_hover_frame",
                    "buttonPressedFrameAssetId": "button_pressed_frame",
                    "buttonDisabledFrameAssetId": "button_disabled_frame",
                    "buttonFrameOpacity": 72,
                    "buttonFrameSlice": {"top": 8, "right": 8, "bottom": 8, "left": 8},
                    "saveSlotFrameAssetId": "save_slot_frame",
                    "systemPanelFrameAssetId": "system_panel_frame",
                    "uiOverlayAssetId": "ui_overlay",
                    "uiOverlayOpacity": 12,
                },
            },
            "assets": {"assets": assets},
            "characters": {
                "characters": [
                    {
                        "id": "heroine",
                        "displayName": "Heroine",
                        "defaultPosition": "center",
                        "expressions": [],
                    }
                ]
            },
            "variables": {"variables": []},
            "chapters": [
                {
                    "id": "chapter_1",
                    "name": "Chapter 1",
                    "scenes": [
                        {
                            "id": "scene_start",
                            "name": "Opening",
                            "blocks": [
                                {"id": "block_bg", "type": "background", "assetId": "title_background"},
                                {
                                    "id": "block_line",
                                    "type": "dialogue",
                                    "speakerId": "heroine",
                                    "voiceAssetId": "voice_missing_line",
                                    "text": "Native Runtime render smoke.",
                                },
                                {
                                    "id": "block_choice",
                                    "type": "choice",
                                    "options": [
                                        {"text": "Continue", "gotoSceneId": ""},
                                        {"text": "Open archive", "gotoSceneId": ""},
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
            "buildInfo": {"exportTargetLabel": "Headless Native Runtime"},
        }
        data_path = self.bundle_dir / "game_data.json"
        data_path.write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")
        return data_path

    def assert_screen_has_pixels(self, player: NativeRuntimePlayer) -> None:
        image_to_bytes = getattr(pygame.image, "tobytes", pygame.image.tostring)
        frame_bytes = image_to_bytes(player.screen, "RGB")
        self.assertTrue(any(channel != 0 for channel in frame_bytes))

    def test_optional_opencv_video_frame_loader_builds_surface(self) -> None:
        class FakeFrame:
            shape = (2, 3, 3)

            def tobytes(self) -> bytes:
                return bytes(
                    [
                        255,
                        0,
                        0,
                        0,
                        255,
                        0,
                        0,
                        0,
                        255,
                        255,
                        255,
                        255,
                        80,
                        120,
                        180,
                        16,
                        24,
                        32,
                    ]
                )

        class FakeCapture:
            def __init__(self, video_path: str) -> None:
                self.video_path = video_path
                self.seek_calls: list[tuple[int, float]] = []
                self.released = False

            def isOpened(self) -> bool:
                return True

            def set(self, prop: int, value: float) -> None:
                self.seek_calls.append((prop, value))

            def read(self) -> tuple[bool, FakeFrame]:
                return True, FakeFrame()

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_POS_MSEC = 101
            COLOR_BGR2RGB = 202
            last_capture: FakeCapture | None = None

            @classmethod
            def VideoCapture(cls, video_path: str) -> FakeCapture:
                cls.last_capture = FakeCapture(video_path)
                return cls.last_capture

            @staticmethod
            def cvtColor(frame: FakeFrame, color_code: int) -> FakeFrame:
                self.assertEqual(color_code, FakeCv2.COLOR_BGR2RGB)
                return frame

        video_path = self.bundle_dir / "assets" / "video" / "preview.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"fake-video-container")

        surface, status = load_opencv_video_frame_surface(pygame, video_path, 1.5, cv2_module=FakeCv2)

        self.assertEqual(status, "OpenCV 帧预览")
        self.assertIsNotNone(surface)
        self.assertEqual(surface.get_size(), (3, 2))
        self.assertIsNotNone(FakeCv2.last_capture)
        self.assertEqual(FakeCv2.last_capture.seek_calls, [(FakeCv2.CAP_PROP_POS_MSEC, 1500.0)])
        self.assertTrue(FakeCv2.last_capture.released)

    def test_video_preview_probe_reports_ready_with_optional_backend(self) -> None:
        self.write_game_data()

        class FakeFrame:
            shape = (2, 3, 3)

            def tobytes(self) -> bytes:
                return bytes([255, 255, 255] * 6)

        class FakeCapture:
            def __init__(self, video_path: str) -> None:
                self.video_path = video_path

            def isOpened(self) -> bool:
                return True

            def set(self, prop: int, value: float) -> None:
                return None

            def read(self) -> tuple[bool, FakeFrame]:
                return True, FakeFrame()

            def release(self) -> None:
                return None

        class FakeCv2:
            CAP_PROP_POS_MSEC = 101
            COLOR_BGR2RGB = 202

            @staticmethod
            def VideoCapture(video_path: str) -> FakeCapture:
                return FakeCapture(video_path)

            @staticmethod
            def cvtColor(frame: FakeFrame, color_code: int) -> FakeFrame:
                return frame

        report = build_native_video_preview_probe_report(self.bundle_dir, pygame_module=pygame, cv2_module=FakeCv2)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["summary"]["videoAssetCount"], 1)
        self.assertEqual(report["summary"]["successCount"], 1)
        self.assertEqual(report["entries"][0]["status"], "ready")
        self.assertEqual(report["entries"][0]["surfaceSize"], {"width": 3, "height": 2})

    def test_native_runtime_renders_ui_skin_overlays_headlessly(self) -> None:
        data_path = self.write_game_data()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        render_steps = [
            lambda: player.render(),
            lambda: (player.open_save_dialog("save"), player.render()),
            lambda: (player.open_save_dialog("load"), player.render()),
            lambda: (player.open_system_menu(), player.render()),
            lambda: (player.open_settings_overlay(), player.render()),
            lambda: (player.open_profile_overlay(), player.render()),
            lambda: (player.open_auto_resume_overlay(), player.render()),
            lambda: (player.open_archive_overlay("chapters"), player.render()),
        ]
        for render_step in render_steps:
            render_step()
            self.assert_screen_has_pixels(player)

        player.start_story_from_title()
        player.render()
        self.assert_screen_has_pixels(player)
        self.assertGreaterEqual(len(player.text_history), 1)
        self.assertTrue(player.font_source_status)
        history_item = player.get_selected_text_history_item()
        self.assertIsNotNone(history_item)
        self.assertEqual(history_item["voiceAssetId"], "voice_missing_line")
        player.play_selected_history_voice()
        self.assertIn("语音素材不可用", player.status_message)
        read_key = str(player.current_line.get("historyKey") or "")
        self.assertTrue(read_key)
        player.mark_current_line_read()
        self.assertIn(read_key, load_project_archive_progress("native_render_smoke")["readTextKeys"])
        snapshot = player.build_save_snapshot("formal")
        self.assertGreaterEqual(len(snapshot["textHistory"]), 1)
        player.text_history = []
        player.text_history_seen_keys = set()
        player.restore_from_snapshot(snapshot)
        self.assertGreaterEqual(len(player.text_history), 1)
        self.assertEqual(player.get_selected_text_history_item()["voiceAssetId"], "voice_missing_line")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            second_player = NativeRuntimePlayer(pygame, data_path)
        self.assertIn(read_key, second_player.read_text_keys)

        player.open_text_history_overlay()
        player.render()
        self.assert_screen_has_pixels(player)
        previous_history_index = player.history_scroll_index
        player.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1}))
        self.assertGreaterEqual(player.history_scroll_index, previous_history_index)
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (0, 0)}))
        self.assertIsNone(player.overlay_mode)
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (0, 0)}))
        self.assertEqual(player.overlay_mode, "system")
        player.close_overlay(preserve_status=True)
        player.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1}))
        self.assertEqual(player.overlay_mode, "history")
        player.close_overlay(preserve_status=True)

        player.toggle_auto_play()
        self.assertTrue(player.auto_play_enabled)
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 2, "pos": (0, 0)}))
        self.assertTrue(player.ui_hidden)
        self.assertFalse(player.auto_play_enabled)
        player.render()
        self.assert_screen_has_pixels(player)
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (0, 0)}))
        self.assertFalse(player.ui_hidden)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_u}))
        self.assertTrue(player.ui_hidden)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_u}))
        self.assertFalse(player.ui_hidden)

        player.toggle_auto_play()
        self.assertTrue(player.auto_play_enabled)
        self.assertFalse(player.skip_read_enabled)
        player.toggle_skip_read()
        self.assertTrue(player.skip_read_enabled)
        self.assertFalse(player.auto_play_enabled)
        player.stop_flow_assist()
        self.assertFalse(player.auto_play_enabled)
        self.assertFalse(player.skip_read_enabled)

        player.overlay_mode = None
        player.current_choices = [
            {"text": "Continue", "gotoSceneId": ""},
            {"text": "Open archive", "gotoSceneId": ""},
        ]
        player.current_choice_index = 1
        player.render()
        self.assert_screen_has_pixels(player)

        video_path = self.bundle_dir / "assets" / "video" / "opening.mp4"
        player.current_choices = None
        player.current_line = {
            "type": "video_play",
            "speakerName": "视频",
            "text": "Video card",
            "videoAssetId": "opening_video",
            "videoAssetPath": str(video_path),
            "videoTitle": "Opening Video",
            "videoFileName": video_path.name,
            "videoStartTimeSeconds": 1.5,
            "videoEndTimeSeconds": 4.0,
            "videoClipLabel": "0:01.5 -> 0:04",
            "videoFit": "contain",
            "videoVolume": 75,
            "videoSkippable": False,
            "videoPreviewMode": "cinematic_bridge_card",
            "videoOpened": False,
        }
        player.render()
        self.assert_screen_has_pixels(player)
        self.assertFalse(player.can_advance_current_line())
        player.current_line["videoOpened"] = True
        self.assertTrue(player.can_advance_current_line())

        selected_entry = player.get_selected_archive_entry()
        if selected_entry:
            player.open_archive_detail(selected_entry)
            player.render()
            self.assert_screen_has_pixels(player)


if __name__ == "__main__":
    unittest.main()
