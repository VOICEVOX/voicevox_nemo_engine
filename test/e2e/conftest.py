"""E2E テスト共通の pytest 用 fixtures。"""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from voicevox_engine.app.application import generate_app
from voicevox_engine.core.core_initializer import initialize_cores
from voicevox_engine.engine_manifest import load_manifest
from voicevox_engine.library.library_manager import LibraryManager
from voicevox_engine.preset.preset_manager import PresetManager
from voicevox_engine.setting.setting_manager import SettingHandler
from voicevox_engine.tts_pipeline.song_engine import make_song_engines_from_cores
from voicevox_engine.tts_pipeline.tts_engine import make_tts_engines_from_cores
from voicevox_engine.user_dict.user_dict_manager import (
    DEFAULT_DICT_PATH,
    UserDictionary,
)
from voicevox_engine.utility.path_utility import engine_manifest_path, get_save_dir


def _copy_under_dir(file_path: Path, dir_path: Path) -> Path:
    """指定ディレクトリ下へファイルをコピーし、生成されたファイルのパスを返す。"""
    copied_file_path = dir_path / file_path.name
    shutil.copyfile(file_path, copied_file_path)
    return copied_file_path


@pytest.fixture
def app_params(tmp_path: Path) -> dict[str, Any]:
    """`generate_app` の全ての引数を生成する。"""
    core_manager = initialize_cores(use_gpu=False, enable_mock=True, cpu_num_threads=1)
    tts_engines = make_tts_engines_from_cores(core_manager)
    song_engines = make_song_engines_from_cores(core_manager)
    setting_loader = SettingHandler(tmp_path / "not_exist.yaml")

    # テスト用に隔離されたプリセットを生成する
    preset_path = tmp_path / "presets.yaml"
    _generate_preset(preset_path)
    preset_manager = PresetManager(preset_path)

    # テスト用に隔離されたユーザー辞書を生成する
    user_dict = UserDictionary(
        default_dict_path=_copy_under_dir(DEFAULT_DICT_PATH, tmp_path),
        user_dict_path=_generate_user_dict(tmp_path),
    )

    engine_manifest = load_manifest(engine_manifest_path())
    library_manager = LibraryManager(
        get_save_dir() / "installed_libraries",
        engine_manifest.supported_vvlib_manifest_version,
        engine_manifest.brand_name,
        engine_manifest.name,
        engine_manifest.uuid,
    )

    return {
        "tts_engines": tts_engines,
        "song_engines": song_engines,
        "core_manager": core_manager,
        "setting_loader": setting_loader,
        "preset_manager": preset_manager,
        "user_dict": user_dict,
        "engine_manifest": engine_manifest,
        "library_manager": library_manager,
    }


@pytest.fixture
def app(app_params: dict[str, Any]) -> FastAPI:
    """app インスタンスを生成する。"""
    return generate_app(**app_params)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """HTTP リクエストを VOICEVOX ENGINE へ送信するクライアントを生成する。"""
    return TestClient(app)


def _generate_preset(preset_path: Path) -> None:
    """指定パス下にプリセットファイルを生成する。"""
    contents = [
        {
            "id": 1,
            "name": "サンプルプリセット",
            "speaker_uuid": "7ffcb7ce-00ec-4bdc-82cd-45a8889e43ff",
            "style_id": 0,
            "speedScale": 1,
            "pitchScale": 0,
            "intonationScale": 1,
            "volumeScale": 1,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1,
            "pauseLength": None,
            "pauseLengthScale": 1,
        }
    ]
    with open(preset_path, mode="w", encoding="utf-8") as f:
        yaml.safe_dump(contents, f, allow_unicode=True, sort_keys=False)


def _generate_user_dict(dir_path: Path) -> Path:
    """指定されたディレクトリ下にユーザー辞書ファイルを生成し、生成されたファイルのパスを返す。"""
    contents = {
        "a89596ad-caa8-4f4e-8eb3-3d2261c798fd": {
            "surface": "ｔｅｓｔ１",
            "context_id": 1348,
            "part_of_speech": "名詞",
            "part_of_speech_detail_1": "固有名詞",
            "part_of_speech_detail_2": "一般",
            "part_of_speech_detail_3": "*",
            "inflectional_type": "*",
            "inflectional_form": "*",
            "stem": "*",
            "yomi": "テストイチ",
            "pronunciation": "テストイチ",
            "accent_type": 1,
            "mora_count": 3,
            "accent_associative_rule": "*",
            "cost": 8609,
        },
        "c89596ad-caa8-4f4e-8eb3-3d2261c798fd": {
            "surface": "ｔｅｓｔ２",
            "context_id": 1348,
            "part_of_speech": "名詞",
            "part_of_speech_detail_1": "固有名詞",
            "part_of_speech_detail_2": "一般",
            "part_of_speech_detail_3": "*",
            "inflectional_type": "*",
            "inflectional_form": "*",
            "stem": "*",
            "yomi": "テストニ",
            "pronunciation": "テストニ",
            "accent_type": 1,
            "mora_count": 2,
            "accent_associative_rule": "*",
            "cost": 8608,
        },
    }
    contents_json = json.dumps(contents, ensure_ascii=False)

    file_path = dir_path / "user_dict_for_test.json"
    file_path.write_text(contents_json, encoding="utf-8")

    return file_path
