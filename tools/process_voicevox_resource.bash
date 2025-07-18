set -eux

if [ ! -v DOWNLOAD_RESOURCE_PATH ]; then
    echo "DOWNLOAD_RESOURCE_PATHが未定義です"
    exit 1
fi

# ダミーのキャラクター情報を置き換える
rm -r resources/character_info
cp -r "${DOWNLOAD_RESOURCE_PATH}/voicevox_nemo/character_info" resources/character_info

# キャラクター情報を前処理する
uv run "${DOWNLOAD_RESOURCE_PATH}/scripts/clean_character_info.py" \
    --character_info_dir resources/character_info/

# エンジンマニフェストを統合する
uv run tools/merge_engine_manifest.py \
    engine_manifest.json \
    "${DOWNLOAD_RESOURCE_PATH}/voicevox_nemo/engine/engine_manifest.json" \
    engine_manifest.json

# エンジンとリソースの更新情報を統合する
uv run tools/merge_update_infos.py \
    resources/engine_manifest_assets/update_infos.json \
    "${DOWNLOAD_RESOURCE_PATH}/voicevox_nemo/engine/engine_manifest_assets/update_infos.json" \
    resources/engine_manifest_assets/update_infos.json

# リソースのマニフェストアセットをエンジンのディレクトリへ複製する
for f in "${DOWNLOAD_RESOURCE_PATH}"/voicevox_nemo/engine/engine_manifest_assets/*; do
    if [ "$(basename "${f}")" != "update_infos.json" ]; then
        cp "${f}" ./resources/engine_manifest_assets/
    fi
done
