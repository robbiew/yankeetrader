# Yankee Trader 3.6 art and menu reference

Open `index.html` for the gallery.

- `originals/`: byte-for-byte copies of YTOPEN.ANS, YTOPEN.ASC, and YTINSTR.DOC.
- `decoded/`: UTF-8 versions decoded from DOS CP437.
- `menus/`: eight readable menu groups, with matching JSON recording every literal's original byte offset, length, and raw bytes.
- `strings/` and `strings.json`: literal catalogs from the game, configuration, initializer, maintenance, and reset executables. These include prompts, display fragments, box-drawing characters, sound strings, and implementation strings.
- `dos-captures/`: 130 existing DOS session logs decoded as CP437, with line endings normalized. Consult these for displayed screens, dynamic data, tables, and conditional behavior.
- `manifest.json`: original file hashes and capture provenance.

## Extraction and limits

Run `python3 analysis/art-menus/extract.py` from the project root to rebuild.

The extractor identifies the dominant QuickBASIC literal pointer base in each executable, then reads matching length/pointer descriptors. This avoids the pointer bytes and trailing metadata attached to text by a generic strings scan. Each catalog records its pointer base and original executable SHA-256.

The gallery renders the original opening ANSI at 80 columns with CP437 characters, DOS colors, and cursor movement. Its font is a modern monospace font, not a recovered DOS bitmap font. The ASCII opening is also preserved.

Menu groups contain original wording in literal order. They are reference transcriptions, not complete screen emulations: display routines supply placement, colors, values, repetitions, and conditional visibility. Sysop configuration fragments in particular contain gaps for runtime values. Original spelling is retained. The initial literal extraction did not run new DOS sessions. The subsequent `screen-recovery/` reference captures run the original binaries against copied fixtures to recover character positions and color attributes. See its README for scope and reproduction. Existing session logs are fixture evidence and do not establish exhaustive screen coverage.

Original source files are read only and are never rewritten by the extractor.
