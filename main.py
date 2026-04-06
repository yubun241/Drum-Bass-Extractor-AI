import os
import torch
import torchaudio
import torchaudio.functional as F
from demucs.separate import main as demucs_separate

# ==========================================
# 【マニュアル設定：ここを調整して実行してください】
# ==========================================
CONFIG = {
    "input_mp3": "sample_music.mp3",   # 元のMP3ファイル名
    "output_name": "drum_bass_cut.wav", # 保存するファイル名
    
    # 周波数のカット設定 (Hz)
    "low_cut_hz": 40,      # これ以下の超低音をカット（スッキリさせたい場合）
    "high_cut_hz": 5000,   # これ以上の高音をカット（ギター等の残響を消したい場合）
    
    # AIの設定
    "model": "htdemucs",   # 分離精度モデル
    "volume_boost": 1.2    # 保存時の音量倍率 (1.0が等倍)
}
# ==========================================

def save_filtered_audio():
    input_file = CONFIG["input_mp3"]
    
    # 1. AI分離の実行
    print(f"--- 1. AIによる音源分離を開始します ({input_file}) ---")
    if not os.path.exists(input_file):
        print(f"エラー: {input_file} が見つかりません。")
        return

    # Demucs実行（一時フォルダに分離音源を書き出し）
    temp_out_dir = "temp_separated"
    demucs_separate(["-n", CONFIG["model"], "--out", temp_out_dir, input_file])

    # 分離されたファイルのパスを取得
    basename = os.path.splitext(os.path.basename(input_file))[0]
    separated_path = os.path.join(temp_out_dir, CONFIG["model"], basename)
    
    # 2. ドラムとベースの読み込みと結合
    print("--- 2. ドラムとベースを抽出・結合しています ---")
    combined_waveform = None
    sample_rate = 0

    for part in ["drums", "bass"]:
        part_file = os.path.join(separated_path, f"{part}.wav")
        if os.path.exists(part_file):
            waveform, sr = torchaudio.load(part_file)
            sample_rate = sr
            if combined_waveform is None:
                combined_waveform = waveform
            else:
                combined_waveform += waveform

    if combined_waveform is None:
        print("エラー: 楽器の抽出に失敗しました。")
        return

    # 3. 周波数フィルタ（カット）の適用
    print(f"--- 3. 周波数カット適用中 ({CONFIG['low_cut_hz']}Hz - {CONFIG['high_cut_hz']}Hz) ---")
    
    # ローパスフィルタ (高域をカット)
    combined_waveform = F.lowpass_biquad(combined_waveform, sample_rate, CONFIG["high_cut_hz"])
    # ハイパスフィルタ (低域をカット)
    combined_waveform = F.highpass_biquad(combined_waveform, sample_rate, CONFIG["low_cut_hz"])
    
    # 音量の微調整
    combined_waveform = combined_waveform * CONFIG["volume_boost"]

    # 4. 最終音源の保存
    print(f"--- 4. ファイルを保存しています: {CONFIG['output_name']} ---")
    torchaudio.save(CONFIG["output_name"], combined_waveform, sample_rate)
    
    print("\nすべての工程が完了しました！")
    print(f"保存場所: {os.path.abspath(CONFIG['output_name'])}")

if __name__ == "__main__":
    save_filtered_audio()
