# 日本語 locale strings for protoc-java-gen

# generate.sh - errors
ERR_NOT_CONFIGURED="❌ 未設定です。実行してください：/protoc-java-gen:setup"
ERR_PROTOC_NOT_FOUND="❌ protoc が見つからないか実行できません：%PROTOC_PATH%"
ERR_PROTO_DIR_NOT_FOUND="❌ Proto ディレクトリが見つかりません：%PROTO_DIR%"
ERR_PROTO_FILE_NOT_FOUND="❌ Proto ファイルが見つかりません：%PROTO_FILE%"
ERR_NO_CLASSNAME="❌ %PROTO_FILE% に java_outer_classname が見つかりません"
ERR_PROTOC_FAILED="❌ protoc の実行に失敗しました（終了コード %EXIT_CODE%）"
ERR_NO_TARGETS="⚠️  プロジェクト内に %JAVA_FILE% に対応する Java ファイルが見つかりません"

# generate.sh - info
MSG_AVAILABLE_PROTOS="📋 利用可能な .proto ファイル："
MSG_GENERATING="🔧 %PROTO_FILE% から Java を生成 → %JAVA_FILE%"
MSG_UPDATED="  ✅ 更新済み：%TARGET%"
MSG_SKIPPED="  ⏭️  変更なし：%TARGET%"
MSG_SUMMARY="📦 完了！%UPDATED% / %TOTAL% ファイルを更新（%SUBPROJECTS% サブプロジェクト）"
MSG_NO_CHANGES="✅ すべての %TOTAL% ファイルは最新です"

# save-config.sh
MSG_CONFIG_SAVED="✅ 設定を保存しました（protoc: %PROTOC_PATH%、プロジェクト: %PROJECT_ROOT%、proto ディレクトリ: %PROTO_DIR%、言語: %LANG%）"
