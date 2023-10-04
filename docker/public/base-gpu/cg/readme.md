As the Triton base image is too large for CG build task to automatically scan, we are currently hand generating the `cgmanifest.json` with the following steps:

0. Get a Linux machine
1. Build the Dockerfile locally
2. Trim the image
   - Run the image interactively with bash, then `rm /opt/` to get rid of the bulk files
   - Export the image and import again to squash layers:
   ```
     docker export <container_id> > image.tar
     cat image.tar | docker import - aml-triton-cg:0
   ```
3. Download the [scanning tool](https://github.com/microsoft/componentdetection-azdo/releases)
4. Scan locally with e.g.
   ```
   dotnet linux-x64/ComponentDetector.dll detect --Verbosity Verbose --Output out --RecordProdTelemetry --SourceDirectory src --SourceFileRoot src --AlertWarningLevel High --DetectorCategories Maven,NuGet,Npm,CgManifest,Rust,Python,CorextCG,Dockerfile,RubyGems,DockerCompose,GoMod,Linux --ScanType LogOnly --TaskVersion 0.2020821.1 --DockerImagesToScan aml-triton-cg:0
   ```
   (Note you need to create the `src/` and `out/` directories beforehand)
5. Find in the `out/` directory a json file that has a format of the `sample.json`
6. Run `python generate_cgmanifest.py <above json>` to finally generate cgmanifest

Reference
- https://docs.opensource.microsoft.com/tools/cg/containers.html
- https://docs.opensource.microsoft.com/tools/cg/cgmanifest.html
- https://github.com/microsoft/componentdetection-azdo/blob/master/docs/detector-arguments.md
