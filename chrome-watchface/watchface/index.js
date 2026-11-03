// Chrome watch face for Zepp OS (round, 480 px design width; px() scales to the actual screen).
// Time, steps, calories and battery all use the system's built-in data bindings, so the watch
// updates them itself: no sensors, timers or polling in this file.

// Asset sizes from tools/gen_assets.py (layout.json)
const BIG_W = 92;     // each time digit (fixed width, so the clock never shifts)
const COLON_W = 30;
const TIME_Y = 142;
const DATA_Y = 352;   // stat numbers
const ICON_Y = 292;   // stat icons (50 x 50)
const DATA_H = 26;
const COLS = [116, 240, 364]; // centres of the steps / calories / battery columns

const range10 = (folder) => [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((d) => `${folder}/${d}.png`);
const TIME_DIGITS = range10('time');
const AOD_DIGITS = range10('time_aod');
const DATA_DIGITS = range10('data');

const TIME_W = 4 * BIG_W + COLON_W;
const HOUR_X = Math.round((480 - TIME_W) / 2);
const MINUTE_X = HOUR_X + 2 * BIG_W + COLON_W;

function timeProps(digits, colon, level) {
  return {
    hour_zero: 1,
    hour_startX: px(HOUR_X),
    hour_startY: px(TIME_Y),
    hour_array: digits,
    hour_space: 0,
    hour_unit_sc: colon,          // the colon is drawn as the hour's "unit" image
    hour_unit_tc: colon,
    hour_unit_en: colon,
    minute_zero: 1,
    minute_startX: px(MINUTE_X),
    minute_startY: px(TIME_Y),
    minute_array: digits,
    minute_space: 0,
    show_level: level,
  };
}

function stat(col, icon, type, unit) {
  const cx = COLS[col];
  hmUI.createWidget(hmUI.widget.IMG, {
    x: px(cx - 25),
    y: px(ICON_Y),
    src: `icons/${icon}.png`,
    show_level: hmUI.show_level.ONLY_NORMAL,
  });
  const props = {
    x: px(cx - 62),
    y: px(DATA_Y),
    w: px(124),
    h: px(DATA_H),
    font_array: DATA_DIGITS,
    h_space: 0,
    align_h: hmUI.align.CENTER_H,
    type,
    show_level: hmUI.show_level.ONLY_NORMAL,
  };
  if (unit) Object.assign(props, { unit_sc: unit, unit_tc: unit, unit_en: unit });
  hmUI.createWidget(hmUI.widget.TEXT_IMG, props);
}

WatchFace({
  init_view() {
    // Normal screen: black dial with chrome bezel and hour ticks
    hmUI.createWidget(hmUI.widget.IMG, {
      x: 0,
      y: 0,
      w: px(480),
      h: px(480),
      src: 'bg.png',
      show_level: hmUI.show_level.ONLY_NORMAL,
    });

    hmUI.createWidget(hmUI.widget.IMG_TIME, timeProps(TIME_DIGITS, 'time/colon.png', hmUI.show_level.ONLY_NORMAL));

    stat(0, 'steps', hmUI.data_type.STEP);
    stat(1, 'cal', hmUI.data_type.CAL);
    stat(2, 'battery', hmUI.data_type.BATTERY, 'data/percent.png');

    // Always-on display: dimmed chrome time only, on a black screen (lowest power)
    hmUI.createWidget(hmUI.widget.IMG_TIME, timeProps(AOD_DIGITS, 'time_aod/colon.png', hmUI.show_level.ONAL_AOD));
  },

  onInit() {},
  build() {},
  onDestroy() {},
});
