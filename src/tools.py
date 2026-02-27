import json
from pathlib import Path

import openpyxl
from agents import function_tool


@function_tool
def read_excel(
    file_path: str,
    sheet_name: str = "",
    start_row: int = 1,
    max_rows: int = 50,
) -> str:
    """Excelファイルを読み込み、ヘッダーと行データを構造化データとして返す。

    Args:
        file_path: Excelファイルの絶対パスまたは相対パス。
        sheet_name: 読み込むシート名。空文字列の場合はアクティブシートを使用する。
        start_row: 読み込み開始データ行番号（1始まり、ヘッダー行の次を1とする）。
        max_rows: 最大読み込み行数（1〜100）。大きなファイルではページネーションに使用する。
    """
    try:
        p = Path(file_path)
        if not p.exists():
            return json.dumps(
                {"error": f"ファイルが見つかりません: {file_path}"},
                ensure_ascii=False,
            )

        wb = openpyxl.load_workbook(str(p), data_only=True, read_only=True)
        try:
            ws = wb[sheet_name] if sheet_name else wb.active
            if ws is None:
                return json.dumps(
                    {"error": "アクティブなシートがありません"},
                    ensure_ascii=False,
                )

            # ヘッダー行（1行目）を読み取る
            headers: list[str] = []
            for cell in ws[1]:
                headers.append(str(cell.value) if cell.value is not None else "")

            if not any(headers):
                return json.dumps(
                    {"error": "シートにデータがありません"},
                    ensure_ascii=False,
                )

            # データ行数を算出
            total_data_rows = ws.max_row - 1 if ws.max_row else 0

            # ページネーション
            max_rows = max(1, min(100, max_rows))
            actual_start = start_row + 1  # Excel行番号（ヘッダーが1行目）
            actual_end = min(actual_start + max_rows - 1, ws.max_row)

            rows = []
            for row in ws.iter_rows(
                min_row=actual_start, max_row=actual_end, values_only=False
            ):
                row_data: dict = {"excel_row": row[0].row}
                for i, cell in enumerate(row):
                    if i < len(headers):
                        key = headers[i] if headers[i] else f"列{i + 1}"
                        row_data[key] = cell.value
                rows.append(row_data)

            returned_count = len(rows)
            return json.dumps(
                {
                    "file": str(p.resolve()),
                    "sheet": ws.title,
                    "headers": headers,
                    "rows": rows,
                    "total_data_rows": total_data_rows,
                    "returned_range": f"{start_row}-{start_row + returned_count - 1} / {total_data_rows}",
                },
                ensure_ascii=False,
                default=str,
            )
        finally:
            wb.close()

    except Exception as e:
        return json.dumps(
            {"error": f"Excelファイルの読み込みに失敗しました: {e}"},
            ensure_ascii=False,
        )


@function_tool
def read_source_code(
    file_path: str,
    start_line: int = 1,
    end_line: int = 0,
) -> str:
    """ファイルを読み込み、指定行範囲の内容を行番号付きで返す。

    Args:
        file_path: ファイルの絶対パスまたは相対パス。
        start_line: 読み込み開始行番号（1始まり）。
        end_line: 読み込み終了行番号。0の場合はstart_lineから50行分を読み込む。
    """
    try:
        p = Path(file_path)
        if not p.exists():
            return json.dumps(
                {"error": f"ファイルが見つかりません: {file_path}"},
                ensure_ascii=False,
            )
        if not p.is_file():
            return json.dumps(
                {"error": f"ファイルではありません: {file_path}"},
                ensure_ascii=False,
            )

        # エンコーディング自動検出（日本語対応）
        content = None
        used_encoding = None
        for enc in ("utf-8", "utf-8-sig", "shift_jis", "cp932", "latin-1"):
            try:
                content = p.read_text(encoding=enc)
                used_encoding = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            return json.dumps(
                {"error": f"ファイルのエンコーディングを検出できません: {file_path}"},
                ensure_ascii=False,
            )

        lines = content.splitlines()
        total_lines = len(lines)

        if end_line <= 0:
            end_line = start_line + 49

        start_line = max(1, start_line)
        end_line = min(end_line, total_lines)

        selected = lines[start_line - 1 : end_line]
        numbered = "\n".join(
            f"{start_line + i}: {line}" for i, line in enumerate(selected)
        )

        return json.dumps(
            {
                "file": str(p.resolve()),
                "start_line": start_line,
                "end_line": end_line,
                "total_lines": total_lines,
                "encoding": used_encoding,
                "content": numbered,
            },
            ensure_ascii=False,
        )

    except PermissionError:
        return json.dumps(
            {"error": f"ファイルの読み込み権限がありません: {file_path}"},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"ファイルの読み込みに失敗しました: {e}"},
            ensure_ascii=False,
        )


@function_tool
def write_excel_cells(
    file_path: str,
    updates_json: str,
    sheet_name: str = "",
) -> str:
    """Excelファイルの指定セルに値を一括書き込みし、ファイルを保存する。

    Args:
        file_path: Excelファイルの絶対パスまたは相対パス。
        updates_json: 書き込むセル情報のJSON配列。形式は [{"row": Excel行番号, "column": "列名", "value": "値"}, ...] とする。
        sheet_name: 書き込むシート名。空文字列の場合はアクティブシートを使用する。
    """
    try:
        p = Path(file_path)
        if not p.exists():
            return json.dumps(
                {"error": f"ファイルが見つかりません: {file_path}"},
                ensure_ascii=False,
            )

        try:
            updates = json.loads(updates_json)
        except json.JSONDecodeError as e:
            return json.dumps(
                {"error": f"updates_jsonのJSON形式が不正です: {e}"},
                ensure_ascii=False,
            )

        if not isinstance(updates, list):
            return json.dumps(
                {"error": "updates_jsonはJSON配列でなければなりません"},
                ensure_ascii=False,
            )

        wb = openpyxl.load_workbook(str(p))
        ws = wb[sheet_name] if sheet_name else wb.active
        if ws is None:
            wb.close()
            return json.dumps(
                {"error": "アクティブなシートがありません"},
                ensure_ascii=False,
            )

        # ヘッダー名 → 列番号のマッピングを構築
        header_map: dict[str, int] = {}
        for col_idx in range(1, ws.max_column + 1):
            val = ws.cell(row=1, column=col_idx).value
            if val is not None:
                header_map[str(val)] = col_idx

        updated_count = 0
        for update in updates:
            row = update.get("row")
            column_name = update.get("column")
            value = update.get("value")

            if row is None or column_name is None:
                continue

            # 列名が存在しなければ新規列を作成
            if column_name not in header_map:
                new_col = ws.max_column + 1
                ws.cell(row=1, column=new_col, value=column_name)
                header_map[column_name] = new_col

            col_idx = header_map[column_name]
            ws.cell(row=row, column=col_idx, value=value)
            updated_count += 1

        wb.save(str(p))
        wb.close()

        return json.dumps(
            {
                "status": "success",
                "updated_cells": updated_count,
                "file": str(p.resolve()),
            },
            ensure_ascii=False,
        )

    except PermissionError:
        return json.dumps(
            {
                "error": f"ファイルが他のプログラムで開かれている可能性があります。Excelを閉じてから再試行してください: {file_path}"
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Excelファイルの書き込みに失敗しました: {e}"},
            ensure_ascii=False,
        )


@function_tool
def list_directory(
    directory_path: str,
    pattern: str = "*",
    recursive: bool = False,
) -> str:
    """ディレクトリ内のファイルとサブディレクトリの一覧を返す。

    Args:
        directory_path: 一覧を取得するディレクトリの絶対パスまたは相対パス。
        pattern: ファイル名フィルタ（globパターン。例: '*.c', '*.py'）。
        recursive: Trueの場合サブディレクトリも再帰的に検索する。パターン例: '*.py' で全階層の.pyファイルを検索できる。
    """
    try:
        p = Path(directory_path)
        if not p.exists():
            return json.dumps(
                {"error": f"ディレクトリが見つかりません: {directory_path}"},
                ensure_ascii=False,
            )
        if not p.is_dir():
            return json.dumps(
                {"error": f"ディレクトリではありません: {directory_path}"},
                ensure_ascii=False,
            )

        if recursive:
            glob_pattern = f"**/{pattern}"
        else:
            glob_pattern = pattern

        entries = sorted(p.glob(glob_pattern))
        dirs = []
        files = []
        limit = 200

        for entry in entries:
            if len(dirs) + len(files) >= limit:
                break
            if entry.is_dir():
                # 再帰時は相対パスを表示
                rel = entry.relative_to(p)
                dirs.append(str(rel) + "/")
            elif entry.is_file():
                rel = entry.relative_to(p)
                files.append(str(rel))

        total = len(dirs) + len(files)
        total_found = len(entries)
        return json.dumps(
            {
                "directory": str(p.resolve()),
                "pattern": pattern,
                "recursive": recursive,
                "directories": dirs,
                "files": files,
                "total_entries": total,
                "truncated": total_found > limit,
                "truncated_note": f"表示は{limit}件までです（全{total_found}件）" if total_found > limit else None,
            },
            ensure_ascii=False,
        )

    except PermissionError:
        return json.dumps(
            {"error": f"ディレクトリの読み込み権限がありません: {directory_path}"},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"ディレクトリの一覧取得に失敗しました: {e}"},
            ensure_ascii=False,
        )


@function_tool
def write_file(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
) -> str:
    """テキストファイルを新規作成または上書き保存する。

    Args:
        file_path: 保存先ファイルの絶対パスまたは相対パス。
        content: ファイルに書き込む内容。
        encoding: 文字エンコーディング。デフォルトは 'utf-8'。日本語Windowsでは 'shift_jis' や 'cp932' も指定可能。
    """
    try:
        p = Path(file_path)

        # 親ディレクトリが存在しない場合は作成
        p.parent.mkdir(parents=True, exist_ok=True)

        p.write_text(content, encoding=encoding)

        return json.dumps(
            {
                "status": "success",
                "file": str(p.resolve()),
                "size_bytes": p.stat().st_size,
                "encoding": encoding,
            },
            ensure_ascii=False,
        )

    except PermissionError:
        return json.dumps(
            {"error": f"ファイルの書き込み権限がありません: {file_path}"},
            ensure_ascii=False,
        )
    except LookupError:
        return json.dumps(
            {"error": f"不明なエンコーディングです: {encoding}（utf-8, shift_jis, cp932 などを指定してください）"},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"ファイルの書き込みに失敗しました: {e}"},
            ensure_ascii=False,
        )
