# Liquid Chrome · JSN (edited prompt)

Liquid Chrome: 6 s seamless loop, 60 fps, 1080x1080, one HTML file, three.js 0.160.0 via jsdelivr importmap only.

window.renderAt(t) sets everything from t in seconds; all motion and noise periodic in 6 s; with ?t= never start requestAnimationFrame; window.__ready after font and bake. Quarter-pixel camera jitter, 4 offsets from frac(t*60).

Raymarch blob, 17 droplets and text as one SDF in a full-screen shader. Smooth-min k 0.35, falling to 0.1 as droplets part; each droplet becomes its glyph through mix(dropSDF, textSDF, K). Text: TextGeometry "JAXON" over "SMITH-NJIGBA" (two centred lines, 17 glyphs including the hyphen, no droplet for the space), per glyph, helvetiker_bold from the pinned examples/fonts, size 0.31, height 0.12 (r160 reads height, not depth), bevel 0.022, 10 bevel and 24 curve segments, tracking 0 em, line gap 0.5 em, hyphen optically centred between H and N. Bake the same outlines into 2048x1024 signed distance textures on the GPU (one channel per glyph), extruded as a rounded box to match the mesh. From 3.3 to 4.7 s cross-fade to the real mesh (creased normals, 35 degrees), same GLSL, reflections traced into the SDF.

Chrome: F0 0.92, Schlick fresnel, roughness 0.04, 3 bounces.

Studio: white floor at y -0.8, soft overhead shadow, contact darkening, 6% reflection, black beyond z 4 (camera side) so letter faces reflect dark. Environment in azimuth and elevation, camera at 0: black camera-side panel 86x57 degrees, softboxes overhead (2.4) and upper left (3.0), black flags at 75 degrees left and right, a 69BE28 (Seahawks action green) rim strip behind at 149 degrees, 24 up, intensity 1.4, a 2 degree glint strip, intensity 6, tilted 40 degrees, sweeping left to right 3.3 to 4.1 s.

Timeline:
0 to 1.2 s: blob radius 0.62 breathes 3% every 1.5 s, simplex noise 0.05.
1.2 to 1.4 s: squash 10%.
1.4 to 2.1 s: stretch 2.4x wide and pinch into 17 droplets sized by glyph area; each arcs 0.2 up to its glyph on its line, overshoots 7%, stretches along its velocity.
2.2 to 3.0 s: droplets become letters, JAXON first then SMITH-NJIGBA, left to right, 2 frames apart, 0.3 s each; bevels start 0.07 puffy and spring flat.
3.0 to 4.8 s: hold.
4.8 s: 6-frame swell, letters slump 0.12 and soften, drain to the center with ease-in, merge at 5.62 s with a 3-bounce wobble (14%, damping 0.25) running through frame 0.

Camera: 30 degree lens, dolly 5.6 to 7.2 by 2.6 s, push to 6.95 in the hold, back to 5.6 by 5.9 s; orbit 7 degrees each way centered on the hold; 6 degrees above.

Post: bloom threshold 1.0, strength 0.3; tone curve linear to 0.9, then a soft shoulder; vignette 7%; grain 1.5% seeded by frame index.
