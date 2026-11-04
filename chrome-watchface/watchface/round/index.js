// Round screens. Layout numbers: ../layouts.js; images: assets/common.r/
import { buildFace } from '../face';
import { ROUND } from '../layouts';

WatchFace({
  init_view() {
    buildFace(ROUND);
  },
  onInit() {},
  build() {},
  onDestroy() {},
});
