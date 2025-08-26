<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Fit Checker — 브랜드별 사이즈 핏 예측</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    *{box-sizing:border-box}html,body{margin:0;padding:0}body{
      font-family:'Pretendard',system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',sans-serif;
      color:#111;background:#f6f7fb
    }
    .container{max-width:980px;margin:0 auto;padding:24px}
    header h1{margin:0 0 8px 0;font-size:28px}
    .sub{margin:0;color:#555}
    .card{background:#fff;border-radius:16px;padding:20px;margin:18px 0;box-shadow:0 4px 14px rgba(0,0,0,.06)}
    .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
    @media(max-width:760px){.grid{grid-template-columns:1fr}}
    label{display:flex;flex-direction:column;gap:6px;font-weight:600}
    input,select,button{font-size:16px;padding:10px 12px;border:1px solid #dcdfe6;border-radius:10px;background:#fff}
    input:focus,select:focus,button:focus{outline:2px solid #3b82f6;outline-offset:2px}
    button{cursor:pointer;border:1px solid #111;background:#111;color:#fff}
    button.ghost{background:#fff;color:#111;border-color:#111}
    button + button{margin-left:10px}
    .row{display:flex;align-items:center;gap:12px;margin-top:10px;flex-wrap:wrap}
    .prefs{display:flex;align-items:center;gap:14px;margin-top:10px}
    .muted{color:#666}.small{font-size:13px}
    .result{margin-top:14px;padding:14px;border-radius:12px;background:#f1f5ff;border:1px solid #dbe7ff}
    .result h3{margin:0 0 6px 0}
    .badge{display:inline-block;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700;margin-right:8px}
    .badge.ok{background:#e7f7ee;color:#0f8b4c;border:1px solid #b3ebcd}
    .badge.warn{background:#fff8e6;color:#a86c00;border:1px solid #fde2a8}
    .badge.err{background:#ffecec;color:#b91c1c;border:1px solid #ffc4c4}
    .multi .brand-block{border:1px dashed #cfd8ea;border-radius:12px;padding:12px;margin:8px 0;background:#fbfcff}
    .multi h4{margin:0 0 6px 0}
    .code{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono','Courier New',monospace}
  </style>
</head>
<body>
  <header class="container">
    <h1>👕 Fit Checker</h1>
    <p class="sub">브랜드/사이즈 + 내 스펙(키/몸무게/가슴둘레 선택)을 넣으면 핏을 예측해주는 데모 앱</p>
  </header>

  <main class="container">
    <section class="card">
      <h2>1) 내 스펙 입력</h2>
      <div class="grid">
        <label>키 (cm)
          <input id="height" type="number" inputmode="decimal" placeholder="예: 167" />
        </label>
        <label>몸무게 (kg)
          <input id="weight" type="number" inputmode="decimal" placeholder="예: 60" />
        </label>
        <label>가슴둘레 (선택, cm)
          <input id="chest" type="number" inputmode="decimal" placeholder="측정값이 있으면 입력" />
        </label>
      </div>

      <div class="prefs">
        <span>핏 선호:</span>
        <label><input type="radio" name="pref" value="slim">슬림</label>
        <label><input type="radio" name="pref" value="regular" checked>레귤러</label>
        <label><input type="radio" name="pref" value="oversized">오버사이즈</label>
      </div>

      <div class="row">
        <button id="saveProfile" class="ghost">내 스펙 저장하기</button>
        <button id="loadProfile" class="ghost">불러오기</button>
        <span id="profileMsg" class="muted"></span>
      </div>
    </section>

    <section class="card">
      <h2>2) 브랜드 & 사이즈 선택</h2>
      <div class="grid">
        <label>브랜드
          <select id="brand"></select>
        </label>
        <label>카테고리
          <select id="category"></select>
        </label>
        <label>사이즈
          <select id="size"></select>
        </label>
      </div>
      <p class="muted small">※ 현재 데이터셋은 남성/유니섹스 상의 기준의 <b>대략적인</b> 바디 가슴둘레 범위(cm)입니다. 브랜드/라인/연식에 따라 다를 수 있어요.</p>
      <div class="row">
        <button id="checkFit">이 사이즈로 핏 예측</button>
      </div>
      <div id="result" class="result"></div>
    </section>

    <section class="card">
      <h2>3) 내 스펙으로 브랜드별 추천 사이즈 찾기</h2>
      <div class="row">
        <button id="findMySize">브랜드별 추천 보기</button>
      </div>
      <div id="multiResults" class="multi"></div>
    </section>

    <section class="card">
      <h2>데이터/알고리즘 설명 (발표용)</h2>
      <details>
        <summary>간단 설명 펼치기</summary>
        <ul>
          <li><b>데이터:</b> 코드 하단의 <code>SIZE_DATA</code>에 브랜드·사이즈별 <i>권장 바디 가슴둘레 범위(cm)</i>를 저장했습니다. (학습용 임시값)</li>
          <li><b>가슴둘레 추정:</b> 가슴둘레를 직접 입력하지 않으면, <code>height</code>와 <code>weight</code>로 추정합니다.<br>
            <code>BMI = kg / (m^2)</code>이고, <code>추정가슴둘레 = 0.54×키(cm) + 1.2×(BMI−22)</code> 를 사용합니다.</li>
          <li><b>핏 판정:</b> 내(추정) 가슴둘레가 해당 사이즈의 권장 범위에 있으면 <b>정사이즈</b>, 범위보다 작으면 <b>여유</b>, 크면 <b>타이트</b>로 표시.
            취향(슬림/레귤러/오버사이즈)에 따라 ± 허용오차를 다르게 적용.</li>
          <li><b>한계:</b> 제품 컷/원단/개인 체형에 따라 착용감은 달라질 수 있어요. 실제 구매 전에는 각 브랜드 공식 사이즈 가이드 확인 권장.</li>
        </ul>
      </details>
    </section>

    <footer class="container muted small">
      <p>© 2025 Fit Checker — School Demo. 데이터는 예시이며 수정 가능. GitHub Pages로 바로 배포할 수 있습니다.</p>
    </footer>
  </main>

  <script>
    // ===== 예시 데이터셋 (남성/유니섹스 상의, '바디 가슴둘레' 권장 범위 cm) =====
    const SIZE_DATA = {
      "Nike": {
        "tops_men_unisex": { "XS":[81,88], "S":[88,96], "M":[96,104], "L":[104,112], "XL":[112,124], "XXL":[124,136] }
      },
      "adidas": {
        "tops_men_unisex": { "XS":[82,87], "S":[88,94], "M":[95,102], "L":[103,111], "XL":[112,121], "XXL":[122,132] }
      },
      "UNIQLO": {
        "tops_men_unisex": { "XS":[80,88], "S":[85,92], "M":[88,96], "L":[96,104], "XL":[104,112], "XXL":[112,120] }
      },
      "ZARA": {
        "tops_men_unisex": { "XS":[88,92], "S":[92,96], "M":[96,100], "L":[100,104], "XL":[104,108], "XXL":[108,112] }
      }
    };

    // ===== 요소 참조 =====
    const brandSel = document.getElementById('brand');
    const catSel   = document.getElementById('category');
    const sizeSel  = document.getElementById('size');
    const resultEl = document.getElementById('result');
    const multiEl  = document.getElementById('multiResults');
    const heightEl = document.getElementById('height');
    const weightEl = document.getElementById('weight');
    const chestEl  = document.getElementById('chest');
    const saveBtn  = document.getElementById('saveProfile');
    const loadBtn  = document.getElementById('loadProfile');
    const profileMsg = document.getElementById('profileMsg');

    const PREF_TOL = { slim: 2, regular: 4, oversized: 6 }; // 허용 오차 (cm)
    const PREF = () => (document.querySelector('input[name="pref"]:checked')||{}).value || 'regular';

    // ===== utils =====
    const round1 = n => Math.round(n*10)/10;
    const cm = v => Number(v||0);
    function getBMI(h, w){ const m = h/100; if(!m||!w) return null; return w/(m*m); }
    function estimateChest(h, w){ const bmi=getBMI(h,w); if(!bmi||!h) return null; return 0.54*h + 1.2*(bmi-22); }
    function getPrefTol(){ return PREF_TOL[PREF()] || 4; }
    function humanCat(key){ return ({'tops_men_unisex':'상의 (남성/유니섹스)'}[key] || key); }

    function explainFit(myChest, range){
      const [min,max] = range;
      const tol = getPrefTol();
      let badgeClass='ok', label='정사이즈', desc='';

      if(myChest < min - tol){
        badgeClass='warn'; label='여유 (넉넉)';
        desc=`내 가슴둘레가 권장 하한보다 ${round1(min-myChest)}cm 작아요 → 루즈/오버 느낌 가능.`;
      }else if(myChest < min){
        badgeClass='warn'; label='루즈';
        desc=`권장 하한보다 ${round1(min-myChest)}cm 작아요.`;
      }else if(myChest <= max){
        badgeClass='ok'; label='정사이즈';
        desc=`권장 범위(${min}–${max}cm)에 들어와요.`;
      }else if(myChest <= max + tol){
        badgeClass='warn'; label='약간 타이트';
        desc=`권장 상한보다 ${round1(myChest-max)}cm 커요.`;
      }else{
        badgeClass='err'; label='타이트 (작음)';
        desc=`권장 상한보다 ${round1(myChest-max)}cm 커서 꽉 낄 수 있어요.`;
      }
      return {badgeClass,label,desc};
    }

    // ===== 셀렉트 초기화 =====
    function initSelectors(){
      Object.keys(SIZE_DATA).forEach(b=>{
        const opt=document.createElement('option'); opt.value=b; opt.textContent=b;
        brandSel.appendChild(opt);
      });
      updateCategories(); updateSizes();
    }
    function updateCategories(){
      catSel.innerHTML='';
      const b=brandSel.value; if(!b) return;
      Object.keys(SIZE_DATA[b]).forEach(c=>{
        const opt=document.createElement('option'); opt.value=c; opt.textContent=humanCat(c);
        catSel.appendChild(opt);
      });
    }
    function updateSizes(){
      sizeSel.innerHTML='';
      const b=brandSel.value, c=catSel.value; if(!b||!c) return;
      Object.keys(SIZE_DATA[b][c]).forEach(s=>{
        const opt=document.createElement('option'); opt.value=s; opt.textContent=s;
        sizeSel.appendChild(opt);
      });
    }
    brandSel.addEventListener('change', ()=>{ updateCategories(); updateSizes(); });
    catSel.addEventListener('change', updateSizes);

    // ===== 프로필 저장/불러오기 =====
    saveBtn.addEventListener('click', ()=>{
      const h=cm(heightEl.value), w=cm(weightEl.value), c=cm(chestEl.value)||null, pref=PREF();
      if(!h||!w){ profileMsg.textContent='키/몸무게는 필수입니다.'; return; }
      localStorage.setItem('fitProfile', JSON.stringify({h,w,c,pref}));
      profileMsg.textContent='저장됨 ✓'; setTimeout(()=>profileMsg.textContent='',1500);
    });
    loadBtn.addEventListener('click', ()=>{
      const raw=localStorage.getItem('fitProfile');
      if(!raw){ profileMsg.textContent='저장된 프로필이 없어요.'; return; }
      try{
        const {h,w,c,pref}=JSON.parse(raw);
        heightEl.value=h||''; weightEl.value=w||''; chestEl.value=c||'';
        if(pref){ const el=document.querySelector(`input[name="pref"][value="${pref}"]`); if(el) el.checked=true; }
        profileMsg.textContent='불러옴 ✓'; setTimeout(()=>profileMsg.textContent='',1500);
      }catch(e){ profileMsg.textContent='불러오기 오류'; }
    });

    // ===== 버튼 동작 =====
    document.getElementById('checkFit').addEventListener('click', ()=>{
      multiEl.innerHTML='';
      const h=cm(heightEl.value), w=cm(weightEl.value);
      if(!h||!w){ return showResultError('키와 몸무게를 입력해 주세요.'); }

      let myChest=cm(chestEl.value);
      if(!myChest){
        myChest=estimateChest(h,w);
        if(!myChest) return showResultError('가슴둘레 추정 실패. 값을 직접 입력해 주세요.');
      }
      myChest=round1(myChest);

      const b=brandSel.value, c=catSel.value, s=sizeSel.value;
      const range=SIZE_DATA[b]?.[c]?.[s];
      if(!range) return showResultError('선택한 사이즈 데이터를 찾지 못했어요.');

      const {badgeClass,label,desc}=explainFit(myChest, range);
      resultEl.innerHTML = `
        <h3>${b} · ${humanCat(c)} · <span class="code">${s}</span></h3>
        <div class="row">
          <span class="badge ${badgeClass}">${label}</span>
          <span>내 가슴둘레: <b>${myChest}cm</b> (직접 입력 또는 추정)</span>
        </div>
        <p class="muted">${desc}</p>
        <p class="small muted">참고 범위: ${range[0]}–${range[1]}cm · 취향 허용오차 ±${getPrefTol()}cm</p>
      `;
    });

    document.getElementById('findMySize').addEventListener('click', ()=>{
      resultEl.innerHTML='';
      const h=cm(heightEl.value), w=cm(weightEl.value);
      if(!h||!w){ return showMultiError('키와 몸무게를 입력해 주세요.'); }

      let myChest=cm(chestEl.value);
      if(!myChest){
        myChest=estimateChest(h,w);
        if(!myChest) return showMultiError('가슴둘레 추정 실패. 값을 직접 입력해 주세요.');
      }
      myChest=round1(myChest);

      multiEl.innerHTML='';
      Object.entries(SIZE_DATA).forEach(([brand, cats])=>{
        Object.entries(cats).forEach(([catKey, sizes])=>{
          const best=pickBestSize(myChest, sizes);
          const block=document.createElement('div');
          block.className='brand-block';
          block.innerHTML = `
            <h4>${brand} · ${humanCat(catKey)}</h4>
            <div class="row">
              <span class="badge ${best.badgeClass}">${best.label}</span>
              <span>추천: <b>${best.size}</b> (참고 ${best.range[0]}–${best.range[1]}cm)</span>
            </div>
            <p class="muted small">${best.desc}</p>
          `;
          multiEl.appendChild(block);
        });
      });
    });

    function pickBestSize(myChest, sizesObj){
      const tol=getPrefTol();
      const entries=Object.entries(sizesObj).map(([size,range])=>{
        const [min,max]=range, mid=(min+max)/2, diff=Math.abs(myChest-mid);
        let penalty=0;
        if(myChest>max+tol) penalty=(myChest-max);
        else if(myChest<min-tol) penalty=(min-myChest);
        return {size,range,score: diff + penalty*1.2};
      });
      entries.sort((a,b)=>a.score-b.score);
      const best=entries[0];
      const explain=explainFit(myChest, best.range);
      return { size:best.size, range:best.range, ...explain };
    }

    function showResultError(msg){ resultEl.innerHTML=`<p class="muted">${msg}</p>`; }
    function showMultiError(msg){ multiEl.innerHTML=`<p class="muted">${msg}</p>`; }

    // init
    (function init(){
      Object.keys(SIZE_DATA).forEach(b=>{
        const opt=document.createElement('option'); opt.value=b; opt.textContent=b;
        brandSel.appendChild(opt);
      });
      updateCategories(); updateSizes();
    })();
  </script>
</body>
</html>
