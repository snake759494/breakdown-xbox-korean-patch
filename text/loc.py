import re
B={'Main Research Center':'연구센터 본관','Research Center Annex':'연구센터 별관','Botanical Research Facility':'식물 연구시설',
'Terminus 4':'터미너스 4','Underground Facility':'지하 시설','Site Zero':'사이트 제로','Main Research Cente':'연구센터 본관'}
R={'Observation Room':'관찰실','Observation Area':'관찰 구역','Rehab Room 1':'재활실 1','Rehab Room 2':'재활실 2','Rehab Room 3':'재활실 3',
'Rehab Area':'재활 구역','Office 1':'사무실 1','Office Area':'사무 구역','Lounge Corridor':'휴게실 복도','Security Office':'경비실',
'Guard Area':'경비 구역','Lounge':'휴게실','Elevator Hall':'엘리베이터 홀','Office 2':'사무실 2','Office 3':'사무실 3',
'Connecting Corridor':'연결 통로','Cafeteria':'식당','Break Area':'휴식 구역','Reference Room':'자료실','Experiment Room':'실험실',
'Experiment Area':'실험 구역','Elevator Shaft':'엘리베이터 통로','Duct':'덕트','Storeroom':'창고','Research Lab':'연구실',
'Corridor':'복도','Utility Room':'설비실','Stairwell 1':'계단 1','Utility Room 1':'설비실 1','Corridor 1':'복도 1',
'Halon Gas Ctrl Room':'할론가스 제어실','Conference Room':'회의실','Courtyard':'안뜰','Toilet':'화장실','Corridor 2':'복도 2',
'Locker Room':'탈의실','Office':'사무실','Corridor 3':'복도 3','Utility Room 2':'설비실 2','Stairwell 2':'계단 2','Roof':'옥상',
'Dry Area':'건조 구역','Dry Area 1':'건조 구역 1','Dry Area 2':'건조 구역 2','Dry Area 3':'건조 구역 3','Dry Area 4':'건조 구역 4',
'Reception':'안내실','Display Room':'전시실','Ruins':'유적','Terminus 4 Entrance':'터미너스 4 입구','Entry Room':'입구실',
'Site Zero Lab':'사이트 제로 연구실','Storeroom 1':'창고 1','Laser Lab':'레이저 연구실','Security Area':'보안 구역',
"T'lan Research Lab 1":'틀란 연구실 1',"T'lan Research Area":'틀란 연구 구역','α Project Room':'α 프로젝트실','β Project Room':'β 프로젝트실',
'Cognitive Psych. Lab':'인지심리 연구실',"T'lan Research Lab 2":'틀란 연구실 2','Storeroom 2':'창고 2','Cemetery':'묘지',
'Control Room':'제어실','Central Treatment Room':'중앙 처치실','Central Treatment Rm':'중앙 처치실','Exit':'출구','Exit 1':'출구 1','Exit 2':'출구 2',
'Shaft':'수직갱','Tunnel 1':'터널 1','Tunnel 2':'터널 2','Tunnel 3':'터널 3','Tunnel 4':'터널 4','Tunnel 5':'터널 5',
'Maintenance Room':'정비실','Fire Control Room':'방화 제어실','Break Room':'휴게실','Flow Control Room':'유량 제어실',
'Filtration Room A':'여과실 A','Filtration Room B':'여과실 B','Filtration Room C':'여과실 C','Sewer':'하수도','Sewer 1':'하수도 1','Sewer 2':'하수도 2',
'Exhaust Fan':'배기 팬','Storage Room':'저장실','Tunnel Boring Machine':'터널 굴착기','Freight Elevator Top':'화물 엘리베이터 상부',
'Freight Elevator':'화물 엘리베이터','Freight Elev. Bottom':'화물 엘리베이터 하부','Loading Area':'하역장','Entrance':'입구',
'Base Camp':'베이스캠프','Valley 1':'계곡 1','Broken Bridge':'무너진 다리','Valley 2':'계곡 2','Clifftop':'절벽 위','Lakeside':'호숫가',
'Ravine Path':'협곡 길','Elevator Tower':'엘리베이터 탑','Outer Wall':'외벽','Top of Outer Wall':'외벽 위','Silo 1':'사일로 1','silo 2':'사일로 2',
'Base of Silo':'사일로 기저부','Top of Silo':'사일로 정상부','Base of Silo1':'사일로 1 기저부','Base of Silo2':'사일로 2 기저부',
'Top of Silo1':'사일로 1 정상부','Top of Silo2':'사일로 2 정상부','Central Dome':'중앙 돔','Passageway':'통로','Corridor #7':'7번 복도',
'Moving Walkway':'무빙워크','Outside Ruins':'유적 외부','Control Room':'제어실','Nexus Area 1':'넥서스 구역 1','Nexus Area 2':'넥서스 구역 2',
'Nexus Area 3':'넥서스 구역 3','Nexus Core':'넥서스 코어'}
SOLO={'Prologue':'프롤로그','Desert':'사막','Direct Elevator':'직통 엘리베이터','Freight Corridor':'화물 통로','Freight Waypoint':'화물 중계점',
'Freight Yard':'화물 집하장','Helipad':'헬리포트','In the Void...':'허공 속에서...','Time Tube':'타임 튜브','Above the Research Center':'연구센터 상공',
'Above the Research⏎Center':'연구센터 상공'}
def fl(s): return s.replace('F','층') if re.fullmatch(r'\d+F',s) else s
def tr(s):
    s0=s
    if s in SOLO: return SOLO[s]
    if s in B: return B[s]
    m=re.fullmatch(r'Silo (\d), Level (\d)(?::|⏎) ?Site Zero\.?',s)
    if m: return f'사이트 제로⏎사일로 {m[1]} {m[2]}층' if '⏎' in s else f'사이트 제로: 사일로 {m[1]} {m[2]}층'
    m=re.fullmatch(r"(.+?), (\d+F): (.+)",s)
    if m and m[1] in B and m[3] in R: return f'{B[m[1]]} {fl(m[2])}: {R[m[3]]}'
    m=re.fullmatch(r"(.+?), (\d+F)",s)
    if m and m[1] in B: return f'{B[m[1]]} {fl(m[2])}'
    m=re.fullmatch(r"(.+?), (\d+F): (.+)",s)
    if m and m[1] in R and m[3] in B: return f'{B[m[3]]} {fl(m[2])}: {R[m[1]]}'
    m=re.fullmatch(r"(.+?): (.+)",s)
    if m and m[1] in B and m[2] in R: return f'{B[m[1]]}: {R[m[2]]}'
    m=re.fullmatch(r"(\d+F): (.+)",s)
    if m and m[2] in R: return f'{fl(m[1])}: {R[m[2]]}'
    m=re.fullmatch(r"(\d+F)⏎(.+)",s)
    if m and m[2] in B: return f'{B[m[2]]} {fl(m[1])}'
    m=re.fullmatch(r"(.+?) (\d+F) ?⏎(.+)",s)
    if m and m[1] in R and m[3] in B: return f'{R[m[1]]}⏎{B[m[3]]} {fl(m[2])}'
    m=re.fullmatch(r"(.+?) *⏎(\d+F)",s)
    if m and m[1] in R: return f'{R[m[1]]}⏎{fl(m[2])}'
    m=re.fullmatch(r"(.+?), (\d+F) *⏎(.+)",s)
    if m and m[1] in R and m[3] in B: return f'{R[m[1]]}⏎{B[m[3]]} {fl(m[2])}'
    m=re.fullmatch(r"(.+?) *⏎(.+)",s)
    if m and m[1] in R and m[2] in B: return f'{R[m[1]]}⏎{B[m[2]]}'
    return None
