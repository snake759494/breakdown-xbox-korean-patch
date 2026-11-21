# 재빌드

## 준비물

- Python 3.11 이상
- `numpy`, `Pillow`, `av`(PyAV), `opencv-python`
  - `pip install numpy pillow av opencv-python`
- Git for Windows의 bash (빌드 스크립트가 셸 스크립트입니다)
- 원본 일본판 XISO
  - MD5가 `0811289cabddf972b0ce164c97224432`이어야 합니다.
- 글꼴(`docs/FONT_CREDITS.md`). 저장소 최상위의 `fonts/` 폴더에 둡니다.
- (배포 파일을 만들 때) xdelta3

## 순서

원본 ISO를 저장소 최상위에 `orig.iso`로 두고 bash에서 실행합니다.

```bash
SRC_ISO=orig.iso bash tools/buildall.sh 'Breakdown (Korean).iso'
```

`buildall.sh`가 하는 일은 다음과 같습니다.
1. `xiso.py`: 디스크 파일 목록(`files.txt`)을 만듭니다.
2. `mkunits.py`: 원본의 영어 CAP 문자열에서 번역 단위 목록(`units.txt`)을 만듭니다. `text/ko_*.txt`의 번호는 이 목록의 줄 번호입니다.
3. `ext.py`: 타이틀·일시정지 그림(`r_BD00.ast`, `r_PauseMain.ast`)과 동영상을 `orig/`로 꺼냅니다.
4. `mvseg.py`·`mvsub.py`·`xmvmux.py`: 자막 있는 동영상과 자막 없는 동영상을 비교해 자막 구간을 찾고, 자막 없는 영상 위에 `text/mv_*.json`의 한글 자막을 그려 WMV2로 인코딩한 뒤 원본 XMV의 오디오·패킷 구조에 맞춰 다시 묶습니다(`mv/`).
   `mvwarn.py`는 시작 경고 동영상의 가장 밝은 프레임에서 일본어 경고문을 지우고(OpenCV 인페인팅) 한글을 그린 뒤, 프레임마다 원래 밝기 비율을 곱해 페이드를 다시 만듭니다.
5. 원본 ISO를 출력 파일로 복사합니다.
6. `build.py`:
   - 모든 `*.pak`의 CAP 문자열을 한국어로 바꾸고, 필요한 한글 글리프를 시스템·자막 글꼴 텍스처에 그려 넣습니다.
   - `img.py`·`logo.py`로 컨트롤러 설정 라벨, 종료 확인 문구, 타이틀 로고 아래 한글 표기를 그립니다.
   - `mv/`의 동영상을 넣습니다.
   - `envtex.py`로 `text/envspec.py`·`text/envmap.json`대로 배경 텍스처의 일본어를 지우고 한글을 그립니다.

모든 파일은 원래 위치·크기 안에서 덮어쓰므로 ISO 크기와 파일 배치는 원본과 같습니다.

## 배포 파일 만들기

```powershell
xdelta3 -e -0 -S none -A -s orig.iso '.\Breakdown (Korean).iso' Breakdown_Xbox_KO_v1.0.xdelta
```

## 보조 도구

- `envsheet.py 배율 번호...`: 배경 텍스처를 격자와 함께 크게 그려 좌표를 잽니다(`view/tx/b.png`).
- `envprev.py 배율 번호...`: `text/envspec.py`를 적용한 결과를 미리 봅니다(`view/tx/p.png`).
- 두 도구는 텍스처 번호 표 `view/sh/map.json`이 필요합니다. 만드는 법은 `docs/TECHNICAL.md`를 참고하세요.

동영상 인코딩(WMV2) 결과는 PyAV·FFmpeg 버전에 따라 바이트 단위로 조금 달라질 수 있습니다. 그 밖의 파일(문자열·글꼴·그림·배경 텍스처)은 같은 원본에서 항상 같은 결과가 나옵니다.
