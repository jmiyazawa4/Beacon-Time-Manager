/* Browser-only schedule export. jsPDF is vendored locally under vendor/. */
(() => {
  'use strict';
  const NAVY = [8, 30, 66], MUTED = [83, 101, 125], LINE = [218, 226, 236];
  const text = value => String(value ?? '').replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/[–—]/g, '-').replace(/…/g, '...').replace(/↗/g, '');
  function rgb(hex) {
    const safe = /^#[0-9a-f]{6}$/i.test(hex || '') ? hex : '#477dbb';
    return safe.slice(1).match(/../g).map(n => parseInt(n, 16));
  }
  function ink(color) {
    const c = color.map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
    return c[0] * .2126 + c[1] * .7152 + c[2] * .0722 > .179 ? [0, 0, 0] : [255, 255, 255];
  }
  function clock(minutes) {
    const m = ((minutes % 1440) + 1440) % 1440, h = Math.floor(m / 60);
    return `${h % 12 || 12}:${String(m % 60).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
  }
  function build(schedule, options = {}) {
    if (!window.jspdf?.jsPDF) throw Error('PDF tools did not load. Reload the planner and try again.');
    const layout = options.layout || 'grid';
    if (!['grid', 'agenda', 'daily'].includes(layout)) throw Error('Choose a schedule layout.');
    const doc = new window.jspdf.jsPDF({orientation: layout === 'grid' ? 'landscape' : 'portrait', unit: 'pt', format: options.paper === 'a4' ? 'a4' : 'letter', compress: true});
    const W = doc.internal.pageSize.getWidth(), H = doc.internal.pageSize.getHeight(), M = 26;
    doc.setProperties({title: `Beacon schedule - ${schedule.weekLabel}`, author: 'Beacon Time Manager', subject: 'Personal weekly schedule'});
    const wrap = (value, width) => doc.splitTextToSize(text(value), width);
    doc.setFontSize(7);
    const includedVerse = options.includeVerse ? schedule.verse : null;
    const verseLines = includedVerse ? wrap(`${includedVerse.reference} (${includedVerse.translation}) - ${includedVerse.text}`, W - 2 * M) : [];
    const creditLines = includedVerse ? wrap(includedVerse.copyright || '', W - 2 * M) : [];
    const footerSpace = includedVerse ? Math.max(72, verseLines.length * 8 + creditLines.length * 7 + 42) : 40;
    if (footerSpace > H - 220) throw Error('The NIV passage and attribution are too long for this layout. Export without the verse.');
    const bottom = H - footerSpace;
    function short(value, width) {
      let result = text(value);
      if (doc.getTextWidth(result) <= width) return result;
      while (result.length && doc.getTextWidth(result + '...') > width) result = result.slice(0, -1);
      return result + '...';
    }
    function header(label) {
      doc.setTextColor(...NAVY); doc.setFont('helvetica', 'bold'); doc.setFontSize(16);
      doc.text('BEACON TIME MANAGER', M, 34);
      doc.setFontSize(11); doc.text(text(label), M, 53);
      doc.setFont('helvetica', 'normal'); doc.setFontSize(9); doc.setTextColor(...MUTED);
      doc.text(text(schedule.weekLabel), M, 68);
      if (schedule.student) doc.text(short(schedule.student, W * .35), W - M, 34, {align: 'right'});
      doc.setDrawColor(...LINE); doc.line(M, 79, W - M, 79);
    }
    function newPage(label) {doc.addPage(); header(label);}
    function color(event) {return options.grayscale ? [243, 243, 243] : rgb(event.color);}
    function timeLabel(event) {
      return event.allDay ? (event.timeUnknown ? event.timeLabel || 'Time TBA' : 'All day') : event.endKnown ? clock(event.start) + ' - ' + clock(event.end) : clock(event.start);
    }
    if (layout === 'grid') {
      header('Weekly grid');
      const timeW = 43, colW = (W - M * 2 - timeW) / 7, top = 91, headH = 25;
      const special = schedule.days.map(day => day.events.filter(e => e.allDay || e.start < 480));
      const hasSpecial = special.some(items => items.length), noteH = hasSpecial ? 43 : 0;
      const gridTop = top + headH + noteH, step = (bottom - gridTop) / 16;
      schedule.days.forEach((day,d)=>{if(day.holiday){doc.setFillColor(...(options.grayscale?[241,241,241]:day.holiday==='holiday'?[255,247,222]:[237,245,255]));doc.rect(M+timeW+d*colW,top+headH,colW,bottom-top-headH,'F');}});
      doc.setFontSize(8); doc.setFont('helvetica', 'bold');
      doc.setFillColor(237, 243, 250); doc.rect(M, top, W - 2 * M, headH, 'F');
      doc.setTextColor(...NAVY); doc.text('TIME', M + 6, top + 16);
      schedule.days.forEach((day, d) => {
        const x = M + timeW + d * colW;
        doc.text(text(day.shortLabel), x + colW / 2, top + 16, {align: 'center'});
        if (hasSpecial) {
          doc.setFont('helvetica', 'normal'); doc.setFontSize(6.5);
          const lines = special[d].flatMap(e => wrap(timeLabel(e) + ': ' + e.title, colW - 8));
          if (lines.length > 4) lines.splice(3, lines.length - 3, short(lines.slice(3).join(' '), colW - 8));
          doc.text(lines, x + 4, top + headH + 10);
          doc.setFont('helvetica', 'bold'); doc.setFontSize(8);
        }
      });
      doc.setFont('helvetica', 'normal'); doc.setFontSize(7); doc.setDrawColor(...LINE); doc.setLineWidth(.4);
      for (let h = 8; h <= 24; h++) {
        const y = gridTop + (h - 8) * step;
        doc.line(M, y, W - M, y);
        if (h < 24) {doc.setTextColor(...MUTED); doc.text(clock(h * 60).replace(':00', ''), M + 3, y + 11);}
      }
      for (let d = 0; d <= 7; d++) doc.line(M + timeW + d * colW, top, M + timeW + d * colW, bottom);
      schedule.days.forEach((day, d) => {
        const items = day.events.filter(e => !e.allDay && e.start >= 480 && e.start < 1440).map(e => ({...e})).sort((a, b) => a.start - b.start);
        let group = [], end = -1, laneEnds = [];
        const flush = () => {for (const e of group) e.lanes = laneEnds.length; group = []; laneEnds = [];};
        for (const e of items) {
          if (e.start >= end) flush();
          let lane = laneEnds.findIndex(finish => finish <= e.start);
          if (lane < 0) lane = laneEnds.length;
          laneEnds[lane] = e.end; e.lane = lane; group.push(e); end = Math.max(end, e.end);
        }
        flush();
        for (const e of items) {
          const width = (colW - 4) / e.lanes, x = M + timeW + d * colW + 2 + e.lane * width;
          const y = gridTop + (e.start / 60 - 8) * step + 1;
          const height = Math.max(5, (Math.min(1440, e.end) - e.start) / 60 * step - 2), fill = color(e);
          doc.setFillColor(...fill); doc.setDrawColor(...(options.grayscale ? [90, 90, 90] : fill)); doc.roundedRect(x, y, width - 1, height, 2, 2, 'FD');
          doc.setTextColor(...ink(fill)); doc.setFont('helvetica', 'bold'); doc.setFontSize(7);
          const maxLines = Math.max(1, Math.floor((height - 6) / 8));
          const lines = wrap(e.title, Math.max(4, width - 7));
          if (lines.length > maxLines) lines.splice(maxLines - 1, lines.length, short(lines.slice(maxLines - 1).join(' '), Math.max(4, width - 7)));
          if (height >= 10) doc.text(lines, x + 3, y + 8);
          if (height > (lines.length + 1) * 8 + 3) {
            doc.setFont('helvetica', 'normal'); doc.setFontSize(6);
            doc.text(short(timeLabel(e), Math.max(4, width - 7)), x + 3, y + 9 + lines.length * 8);
          }
        }
      });
    } else {
      let y = 96;
      const pageLabel = day => layout === 'daily' ? day.label : 'Weekly agenda';
      header(pageLabel(schedule.days[0]));
      schedule.days.forEach((day, index) => {
        if (layout === 'daily' && index) {newPage(pageLabel(day)); y = 96;}
        if (y + 38 > bottom) {newPage(pageLabel(day)); y = 96;}
        doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.setTextColor(...NAVY);
        if (layout !== 'daily') {doc.text(text(day.label), M, y); y += 19;}
        if (!day.events.length) {
          doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(...MUTED); doc.text('No activities scheduled.', M + 8, y + 9); y += 30;
        }
        day.events.forEach(event => {
          const contentWidth = W - M * 2 - 20;
          doc.setFontSize(layout === 'daily' ? 12 : 10); doc.setFont('helvetica', 'bold');
          const title = wrap(event.title, contentWidth);
          doc.setFont('helvetica', 'normal'); doc.setFontSize(9);
          const detail = wrap([timeLabel(event), event.category, event.location].filter(Boolean).join(' | '), contentWidth);
          const lineH = layout === 'daily' ? 15 : 12, lines = [...title.map(t => ({value: t, bold: true})), ...detail.map(t => ({value: t, bold: false}))];
          // Write line by line so unusually long event names cannot fall off a page.
          for (const line of lines) {
            if (y + lineH + 10 > bottom) {newPage(pageLabel(day) + ' (continued)'); y = 96;}
            doc.setDrawColor(...(options.grayscale ? [95, 95, 95] : rgb(event.color))); doc.setLineWidth(3); doc.line(M + 2, y - 1, M + 2, y + lineH - 1);
            doc.setFont('helvetica', line.bold ? 'bold' : 'normal'); doc.setFontSize(line.bold ? (layout === 'daily' ? 12 : 10) : 9); doc.setTextColor(...(line.bold ? NAVY : MUTED));
            doc.text(line.value, M + 10, y + 9); y += lineH;
          }
          y += layout === 'daily' ? 17 : 11;
        });
        if (layout === 'daily') {
          if (y + 65 < bottom) {
            y += 13; doc.setFont('helvetica', 'bold'); doc.setFontSize(10); doc.setTextColor(...MUTED); doc.text('Notes', M, y); y += 10;
            doc.setDrawColor(...LINE); doc.setLineWidth(.5);
            for (; y + 20 < bottom; y += 22) doc.line(M, y + 13, W - M, y + 13);
          }
        } else y += 14;
      });
    }
    const pages = doc.getNumberOfPages();
    for (let page = 1; page <= pages; page++) {
      doc.setPage(page); doc.setTextColor(...MUTED); doc.setFont('helvetica', 'normal'); doc.setFontSize(7);
      if (includedVerse) {
        const verseY = H - footerSpace + 12;
        doc.setDrawColor(...LINE); doc.setLineWidth(.4); doc.line(M, verseY - 10, W - M, verseY - 10);
        doc.text(verseLines, M, verseY, {lineHeightFactor: 8/7});
        doc.setFontSize(6.5);
        doc.text(creditLines, M, verseY + verseLines.length * 8 + 7, {lineHeightFactor: 7/6.5});
      }
      doc.setFontSize(6.5); doc.text('Competition durations not listed by athletics use a one-hour display block. Confirm changes with athletics.', M, H - 22);
      doc.text(`${page} / ${pages}`, W - M, H - 11, {align: 'right'});
      doc.text('Beacon Time Manager | ' + text(schedule.weekLabel), M, H - 11);
    }
    return doc;
  }
  window.BeaconPDF = {build};
})();
