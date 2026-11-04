// Chrome watch face for Zepp OS (round, 480 px design width; px() scales to the actual screen).
// Time, steps, calories and battery all use the system's built-in data bindings, so the watch
// updates them itself: no sensors, timers or polling in this file.

// Asset sizes from tools/gen_assets.py (layout.json); positions must match its LAYOUT line
const BIG_W = 82;     // each time digit (fixed width, so the clock never shifts)
const COLON_W = 28;
const TIME_Y = 124;
const DATA_Y = 322;   // stat numbers
const ICON_Y = 266;   // stat icons (50 x 50)
const DATA_H = 35;   // digit image height
const DATA_W = 140;  // wide enough for "12408" / "100%" so the watch never crops the text
const COLS = [122, 240, 358]; // centres of the steps / calories / battery columns

const range10 = (folder) => [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((d) => `${folder}/${d}.png`);
const TIME_DIGITS = range10('time');
const AOD_DIGITS = range10('time_aod');
const DATA_DIGITS = range10('data');

const TIME_W = 4 * BIG_W + COLON_W;
const HOUR_X = Math.round((480 - TIME_W) / 2);
const MINUTE_X = HOUR_X + 2 * BIG_W + COLON_W;

// Frosted teal chrome hands (tools/gen_assets.py -> layout.json "HANDS").
// posX / posY = the pivot point inside each hand image; the watch rotates the image about it.
const CENTER = 240;
const CAP = 26;
const HANDS = {
  hour: { posX: 22, posY: 130 },
  minute: { posX: 18, posY: 198 },
  second: { posX: 14, posY: 214 },
};

function hands(suffix, withSeconds, level) {
  const p = {
    hour_centerX: px(CENTER),
    hour_centerY: px(CENTER),
    hour_posX: px(HANDS.hour.posX),
    hour_posY: px(HANDS.hour.posY),
    hour_path: `hands/hour${suffix}.png`,
    minute_centerX: px(CENTER),
    minute_centerY: px(CENTER),
    minute_posX: px(HANDS.minute.posX),
    minute_posY: px(HANDS.minute.posY),
    minute_path: `hands/minute${suffix}.png`,
    show_level: level,
  };
  if (withSeconds) {
    Object.assign(p, {
      second_centerX: px(CENTER),
      second_centerY: px(CENTER),
      second_posX: px(HANDS.second.posX),
      second_posY: px(HANDS.second.posY),
      second_path: 'hands/second.png',
      second_cover_path: 'hands/cap.png', // centre cap sits on top of all three hands (still under the digits)
      second_cover_x: px(CENTER - CAP / 2),
      second_cover_y: px(CENTER - CAP / 2),
    });
  } else {
    Object.assign(p, {
      minute_cover_path: 'hands/cap.png',
      minute_cover_x: px(CENTER - CAP / 2),
      minute_cover_y: px(CENTER - CAP / 2),
    });
  }
  return p;
}

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
    x: px(cx - DATA_W / 2),
    y: px(DATA_Y),
    w: px(DATA_W),
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

    // Analog hands sit on the background, BEHIND the digits and stats (widgets stack in
    // creation order). The system keeps them in sync with the clock.
    hmUI.createWidget(hmUI.widget.TIME_POINTER, hands('', true, hmUI.show_level.ONLY_NORMAL));

    hmUI.createWidget(hmUI.widget.IMG_TIME, timeProps(TIME_DIGITS, 'time/colon.png', hmUI.show_level.ONLY_NORMAL));

    stat(0, 'steps', hmUI.data_type.STEP);
    stat(1, 'cal', hmUI.data_type.CAL);
    stat(2, 'battery', hmUI.data_type.BATTERY, 'data/percent.png');

    // Always-on display: dimmed chrome time + dimmed hour/minute hands on black (lowest power)
    hmUI.createWidget(hmUI.widget.TIME_POINTER, hands('_aod', false, hmUI.show_level.ONAL_AOD)); // dimmed, no second hand
    hmUI.createWidget(hmUI.widget.IMG_TIME, timeProps(AOD_DIGITS, 'time_aod/colon.png', hmUI.show_level.ONAL_AOD));
  },

  onInit() {},
  build() {},
  onDestroy() {},
});
