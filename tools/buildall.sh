#!/usr/bin/env bash
# 사용법: SRC_ISO=orig.iso bash tools/buildall.sh 'Breakdown (Korean).iso'
set -e
cd "$(dirname "$0")/.."
export SRC_ISO="${SRC_ISO:-orig.iso}"
OUT="${1:-Breakdown (Korean).iso}"
export MSYS_NO_PATHCONV=1
mkdir -p build mv
# 1. 디스크 파일 목록과 번역 단위 목록(원문에서 생성, 저장소에는 넣지 않음)
python tools/xiso.py "$SRC_ISO" list | tr -d '\015' > files.txt
python tools/mkunits.py "$SRC_ISO"
# 2. 필요한 원본 파일 추출
python tools/ext.py "$SRC_ISO" orig r_BD00.ast r_PauseMain.ast /romdata/movie/opening_b /romdata/movie/ED_02 /romdata/movie/warning.xmv
M=orig/romdata/movie
# 3. 동영상 자막(영어판 깨끗한 영상 위에 한글 자막을 그려 WMV2로 다시 인코딩)
python tools/mvseg.py $M/opening_b.xmv $M/opening_bt.xmv build/op_seg.json 300 440 > /dev/null
python tools/mvsub.py $M/opening_b.xmv $M/opening_bt.xmv build/op_seg.json text/mv_op.json build/op.pkl 0 24 > /dev/null
python tools/xmvmux.py $M/opening_bt.xmv build/op.pkl mv/opening_bt.xmv c
python tools/mvsub.py $M/opening_b51.xmv $M/opening_bt51.xmv build/op_seg.json text/mv_op.json build/op51.pkl 0 24 > /dev/null
python tools/xmvmux.py $M/opening_bt51.xmv build/op51.pkl mv/opening_bt51.xmv c
python tools/mvseg.py $M/ED_02E.xmv $M/ED_02J.xmv build/ed_seg.json 400 475 > /dev/null
python tools/mvsub.py $M/ED_02E.xmv $M/ED_02J.xmv build/ed_seg.json text/mv_ed.json build/ed.pkl 0 24 > /dev/null
python tools/xmvmux.py $M/ED_02J.xmv build/ed.pkl mv/ED_02J.xmv c
# 시작 경고 화면
python tools/mvwarn.py $M/warning.xmv build/warn.pkl
python tools/xmvmux.py $M/warning.xmv build/warn.pkl mv/warning.xmv c
# 4. 원본을 복사한 뒤 텍스트·글꼴·그림·동영상·배경 텍스처를 덮어쓰기
cp "$SRC_ISO" "$OUT"
python tools/build.py "$OUT"
echo "done: $OUT"
