# Socialia release container configuration

The tag workflow calls `exec-in-sif.sh` for its test, build and publish helpers.
Configure these repository Actions variables for the selected runner:

| Variable | Meaning |
| --- | --- |
| `SCITEX_CI_APPTAINER` | Executable Apptainer path; a leading `~/` resolves under the runner home. |
| `SCITEX_CI_SIF` | Existing CI image path, with the same home expansion. |
| `SCITEX_CI_BINDPATH` | Optional Apptainer binding specification for shared filesystems or symlink targets. |

The wrapper does not assume a particular home environment or GPFS mount.
A configured executable or image that is missing is a hard failure; it does
not switch to a bare-runner install. The executable's directory is added to
`PATH` so a configured environment's shim can find its interpreter.

`APPTAINER_TMPDIR` is respected when set. Otherwise scratch defaults to
`RUNNER_TEMP/scitex-socialia-apptainer`, falling back to the inherited `TMPDIR`
or `/tmp`. Standard `APPTAINER_BINDPATH` is preserved unless the nonempty
`SCITEX_CI_BINDPATH` override is supplied. Existing installations that require
a shared mount must configure that binding explicitly before release.

Behavioral controls in `tests/integration/test_release_sif_paths.py` run the
real wrapper with owned command processes and inert image files. These check
argument boundaries, scratch selection, configured bindings and refusal of
missing runtime paths. They do not qualify a real image, native container
execution, package publication or the runner's mount configuration. Those
release checks remain required.
