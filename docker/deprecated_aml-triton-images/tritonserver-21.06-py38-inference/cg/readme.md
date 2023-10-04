As the Triton base image is too large for CG build task to automatically scan, we are currently hand generating the `cgmanifest.json` with the following steps:

0. Get a Linux machine
1. Build the Dockerfile locally
2. Trim the image
   - Run the image interactively with bash, then `rm /opt/` to get rid of the bulk files
   - Export the image and import again to squash layers:
   ```
     docker export <container_id> > image.tar
     cat image.tar | docker import - tritonserver-21.06-py38-inference-cg:0
   ```
3. Download the [scanning tool](https://github.com/microsoft/componentdetection-azdo/releases)
4. Create temporary local directories 'src/` and `out/` and scan locally.
   ```
   mkdir src out
   dotnet linux-x64/ComponentDetector.dll detect --Verbosity Verbose --Output out --RecordProdTelemetry --SourceDirectory src --SourceFileRoot src --AlertWarningLevel High --DetectorCategories Maven,NuGet,Npm,CgManifest,Rust,Python,CorextCG,Dockerfile,RubyGems,DockerCompose,GoMod,Linux --ScanType LogOnly --TaskVersion 0.2020821.1 --DockerImagesToScan tritonserver-21.02-py38-inference-cg:0
   ```
5. Find in the `out/` directory a file with its name matching GovCompDisc_Manifest_<timestamp>.json.
6. Run `python generate_cgmanifest.py out/GovCompDisc_Manifest_<timestamp>.json` to finally generate cgmanifest.

Reference
- https://docs.opensource.microsoft.com/tools/cg/containers.html
- https://docs.opensource.microsoft.com/tools/cg/cgmanifest.html
- https://github.com/microsoft/componentdetection-azdo/blob/master/docs/detector-arguments.md
