# Changelog

## 0.3.0 — 2026-10-09

- Add start/pause auto-rotation beside Top / Side / Oblique, with selectable
  axis, preview speed and reverse direction.
- Export MP4 and looping GIF turntables from the current view; provide duration,
  frame rate, resolution, full rotations, progress and cancellation.
- Keep color limits fixed throughout each movie, stream frames without retaining
  the whole animation in memory, restore the live camera, and save scene/animation
  sidecars. Include FFmpeg through the GUI dependency.
- Preserve perspective field of view when saving and restoring camera settings.

- Display figure units with superscripts and the Angstrom symbol (eV⁻¹ Å⁻³ or
  keV⁻¹ Å⁻³) in every colorbar layout and exported image.
- Use the author's saved Pt₃Y view at startup, including its camera, perspective
  projection and automatic color limits, matching the selected screenshot and icon.

## 0.2.2 — 2026-10-09

- Add a macOS application installer and one-click setup script. Studio opens
  from Applications or Spotlight and starts with the Pt₃Y demo.
- Add a transparent Pt₃Y application icon for Finder, the Dock and GUI windows.
- Preserve virtual-environment interpreter paths, protect unrelated app bundles
  during installation, and record startup errors in the user's Library/Logs.

## 0.2.1 — 2026-10-09

- Simplify the Pt₃Y descriptions across the landing pages, guides, desktop demo
  catalog and release notes; retain calculation parameters and numerical reports.
- Refresh the desktop screenshot and bilingual installation instructions.
- Generate CLI reference version headings from the package version.

## 0.2.0 — 2026-10-09

- Complete English and Chinese user/developer manuals, numerical and Bader
  references, troubleshooting, software scope and release notes.
- Generate both CLI references from the actual parser and check local links in CI.
- Prepare the initial Git/GitHub archive and reproducible release packages.
- Fix Windows reopening of decompressed PARCHG temporary files; read the demo
  catalog as UTF-8 independently of the operating-system locale.

- Add a dedicated Style tab with scientific, paper-style, presentation and
  grayscale presets; horizontal, vertical, compact, endpoint and hidden bars;
  fonts, ticks, formatting, reversed palettes and eV/keV display conversion.
- Add an offline demonstration catalog with explicit data provenance.
- Add the official Henkelman Bader integration workflow, reference-density
  fingerprints, grid alignment, atomic tables, conservation checks and basin
  selection/export. Include a checksum-verified optional Bader installer.
- Recover the author's local SI and manuscript archive; establish Pt3Y(111)
  reconstruction and strict original-result comparison as separate evidence gates.

## 0.1.0 — 2026-10-08

Initial standalone WAVECAR and native-PARCHG engines, scientific viewer,
CLI, Cube and figure export, public fixtures and a real VASP Pt(111) benchmark.
