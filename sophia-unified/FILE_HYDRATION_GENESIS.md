# File Hydration Genesis

The file is not swallowed into the foreground.

The file emanates a small carrier:

```text
file metadata
  -> file hydration atom
  -> compatibility membrane
  -> OPTE-shaped receipt
  -> later aperture match
```

Each file atom carries:

- a path hint
- suffix
- size band
- source realm
- local motifs
- affordances
- compatibility requirements
- fallback residual behaviour

Known files offer apertures.  Unknown files seek apertures.  Nothing has to be
fully compatible at ingress.

```text
unsupported != dead
unsupported == airborne residual seeking the right lens
```

The API endpoint accepts metadata only:

```text
POST /v1/files/hydrate
```

It does not read file contents.  A trusted local adapter may call `from_path()`
to read `stat` metadata and produce the same file signal.
