// Square screens. Layout numbers: ../layouts.js; images: assets/square.s/
import { buildFace } from '../face';
import { SQUARE } from '../layouts';

WatchFace({
  init_view() {
    buildFace(SQUARE);
  },
  onInit() {},
  build() {},
  onDestroy() {},
});
