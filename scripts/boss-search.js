// 在已打开 zhipin.com 的页面上下文里执行(devtools console / 浏览器 agent 的 evaluate)。
// 返回:去重、过滤后的候选数组,每行 "岗位|薪资|公司|城市+区|年限|学历|技能|jobId"。
// 改 CITIES / KEYWORDS 即可。
// 频率(2026-10-28 定的,血泪):**一次最多 10 条、每批之间隔 30 分钟、请求之间隔 8 秒**。
// 前一天翻太密,BOSS 直接把这个 IP 封了几天。下面是照这个写的默认值,别自己调快。

(async () => {
  const CITIES = {
    '101190100': '南京',
    // '101190400': '苏州', '101190200': '无锡', '101191100': '常州', '101190900': '淮安', '101190800': '徐州',
  };
  const KEYWORDS = ['视觉算法'];   // 一次只跑一个词;下一个词等 30 分钟再跑
  const MAX_ROWS = 10;             // 一批最多收 10 条,满了就停
  const MAX_EXP = ['5-10年', '10年以上'];      // 年限过高的直接丢
  const MIN_SALARY_K = 10;                      // 月薪下限(万→这里用 K);未登录时薪资为空,不做过滤
  const WANT = /视觉|图像|检测|配准|机器视觉|点云|三维/;

  const parseSalary = s => {
    if (!s) return null;
    const m = s.match(/(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)K/);
    return m ? [parseFloat(m[1]), parseFloat(m[2])] : null;
  };

  const seen = new Set(), rows = [], errors = [];
  for (const code of Object.keys(CITIES)) {
    if (rows.length >= MAX_ROWS) break;
    for (const q of KEYWORDS) {
      if (rows.length >= MAX_ROWS) break;
      const url = '/wapi/zpgeek/search/joblist.json?scene=1&query=' +
        encodeURIComponent(q) + '&city=' + code + '&page=1&pageSize=10';
      let d;
      try {
        const r = await fetch(url, { credentials: 'include' });
        d = await r.json();
      } catch (e) { errors.push(code + '/' + q + ' 网络错误'); continue; }
      if (d.code !== 0) { errors.push(code + '/' + q + ' → ' + d.code + ' ' + d.message); continue; }
      for (const j of ((d.zpData || {}).jobList || [])) {
        if (rows.length >= MAX_ROWS) break;
        if (!j.encryptJobId || seen.has(j.encryptJobId)) continue;
        seen.add(j.encryptJobId);
        if (MAX_EXP.includes(j.jobExperience)) continue;
        const blob = (j.jobName || '') + ' ' + (j.skills || []).join('/');
        if (!WANT.test(blob)) continue;
        const sal = parseSalary(j.salaryDesc);
        if (sal && sal[1] < MIN_SALARY_K) continue;
        rows.push([
          j.jobName, j.salaryDesc || '(未登录不可见)', j.brandName,
          j.cityName + (j.areaDistrict || '') + (j.businessDistrict || ''),
          j.jobExperience || '-', j.jobDegree || '-',
          (j.skills || []).join('/'), j.encryptJobId
        ].join('|'));
      }
    }
  }
  // 出现 code 35 / 异常行为就停下,今天这批到此为止
  return { count: rows.length, errors, rows };
})()
