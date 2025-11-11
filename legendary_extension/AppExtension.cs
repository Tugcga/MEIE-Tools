using Microsoft.AspNetCore;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http.Extensions;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using TerraFX.Interop.Windows;
using System.Text.Json;
using System.Text;
using LegendaryExplorerCore.Gammtek.Paths;
using LegendaryExplorerCore.Packages;
using LegendaryExplorerCore.GameFilesystem;
using LegendaryExplorerCore.UDK;
using System.Collections.Generic;
using LegendaryExplorerCore.Gammtek.Extensions;
using LegendaryExplorerCore.Unreal.BinaryConverters;
using LegendaryExplorerCore.Unreal;
using SharpDX.DXGI;
using LegendaryExplorer.Tools.SequenceObjects;
using System.Numerics;
using SharpDX.Direct2D1.Effects;
using System.ComponentModel.Composition.Primitives;
using CliWrap;
using LegendaryExplorer.Misc;
using Microsoft.VisualStudio.TestPlatform.Utilities;
using Piccolo.Nodes;
using LegendaryExplorerCore.Helpers;
using LegendaryExplorerCore.Unreal.Classes;
using LegendaryExplorerCore.Packages.CloningImportingAndRelinking;
using System.Windows.Media.Media3D;
using LegendaryExplorer.UserControls.ExportLoaderControls.MaterialEditor;
using CommunityToolkit.Diagnostics;
using DocumentFormat.OpenXml.InkML;
using LegendaryExplorerCore.Gammtek.Extensions.Collections.Generic;

public class WebServer
{
    private IWebHost _host;

    string MatrixToString(Matrix4x4 matrix, char fs = ' ')
    {
        return matrix.M11.ToString() + fs + matrix.M12.ToString() + fs + matrix.M13.ToString() + fs + matrix.M14.ToString() + fs +
            matrix.M21.ToString() + fs + matrix.M22.ToString() + fs + matrix.M23.ToString() + fs + matrix.M24.ToString() + fs +
            matrix.M31.ToString() + fs + matrix.M32.ToString() + fs + matrix.M33.ToString() + fs + matrix.M34.ToString() + fs +
            matrix.M41.ToString() + fs + matrix.M42.ToString() + fs + matrix.M43.ToString() + fs + matrix.M44.ToString();
    }

    string GetLocations(string levelPcc)
    {
        // return pcc-files in the format pcc1#pcc2#...
        string output = levelPcc;
        IMEPackage pcc = MEPackageHandler.OpenMEPackage(levelPcc);
        if (pcc is MEPackage mePackage)
        {
            var loadedFiles = MELoadedFiles.GetFilesLoadedInGame(pcc.Game);

            foreach (string additionalPackage in mePackage.AdditionalPackagesToCook)
            {
                if (loadedFiles.TryGetValue($"{additionalPackage}.pcc", out string filePath))
                {
                    using IMEPackage levPcc = MEPackageHandler.OpenMEPackage(filePath);
                    output += "#" + levPcc.FilePath;
                }
            }
        }
        return output;
    }

    string GetStaticMeshes(string pccPath)
    {
        IMEPackage pcc = MEPackageHandler.OpenMEPackage(pccPath);
        string output = "";

        string assetsOutputPath = "";
        string decookedMaterialsFolder = "";
        var assetInfo = ConvertToUDK.GenerateAssetsPackage(pcc, assetsOutputPath, decookedMaterialsFolder);
        for (int i = 0; i < assetInfo.StaticMeshes.Count; i++)
        {
            ExportEntry entry = assetInfo.StaticMeshes[i];
            string rawPath = entry.InstancedFullPath;
            output += rawPath.Substring(13) + "#";
        }

        return output.Length > 0 ? output.Substring(0, output.Length - 1) : "";
    }

    string ExportMaterials(IMEPackage pcc, StaticMesh bin, ExportEntry entry, string texturesPath)
    {
        string output = "";
        int matIndex = 0;
        foreach (var mat in bin.GetMaterials())
        {
            // start material section from the identifier index...
            output += "%index" + matIndex.ToString() + "#";
            if (entry.FileRef.TryGetEntry(mat, out var matEntry))
            {
                ExportEntry exp = matEntry as ExportEntry;
                if (exp == null)
                {
                    ImportEntry imp = matEntry as ImportEntry;
                    EntryImporter.TryResolveImport(imp, out exp);
                    pcc = exp.FileRef;
                }

                // set the key, that this material is export
                output += "export#";
                // the name
                output += exp.ObjectNameString + "#";

                MaterialInfo mInfo = new MaterialInfo();
                mInfo.MaterialExport = exp;
                mInfo.HostingControlGuid = Guid.NewGuid();
                PackageCache initialPackageCache = new PackageCache();
                mInfo.InitMaterialInfo(initialPackageCache);

                output += "textures#";
                var textures = mInfo.UniformTextures;
                foreach (var texture in textures)
                {
                    ExportEntry textureEntry = texture.TextureExp;
                    if (textureEntry != null)
                    {
                        output += textureEntry.ObjectNameString + "#";
                        Texture2D t2d = new Texture2D(textureEntry);
                        t2d.ExportToPNG(texturesPath + textureEntry.ObjectNameString + ".png");
                    }
                }

                output += "expressions#";
                // next we should write all parameters
                var expressions = mInfo.Expressions;
                foreach (var expression in expressions)
                {
                    string name = expression.ParameterName;

                    var type = expression.GetType();
                    string typeStr = type.ToString();
                    if (typeStr == "LegendaryExplorer.UserControls.ExportLoaderControls.MaterialEditor.ScalarParameterMatEd")
                    {
                        output += name + "#";

                        var scalar = expression as ScalarParameter;
                        output += "scalar#";
                        output += scalar.ParameterValue.ToString() + "#";
                    }
                    else if (typeStr == "LegendaryExplorer.UserControls.ExportLoaderControls.MaterialEditor.VectorParameterMatEd")
                    {
                        output += name + "#";

                        var vector = expression as VectorParameter;
                        output += "vector#";
                        output += vector.ParameterValue.W.ToString() + "%";
                        output += vector.ParameterValue.X.ToString() + "%";
                        output += vector.ParameterValue.Y.ToString() + "%";
                        output += vector.ParameterValue.Z.ToString() + "#";
                    }
                    else if (typeStr == "LegendaryExplorer.UserControls.ExportLoaderControls.MaterialEditor.TextureParameterMatEd")
                    {
                        var texture = expression as TextureParameter;
                        // we should get texture entry by it index
                        ExportEntry textureEntry = pcc.GetEntry(texture.ParameterValue) as ExportEntry;
                        if (textureEntry != null && textureEntry.ClassName != "TextureCube")
                        {
                            output += name + "#";
                            output += "texture#";
                            output += textureEntry.ObjectNameString + "#";

                            Texture2D t2d = new Texture2D(textureEntry);
                            // export the texture
                            t2d.ExportToPNG(texturesPath + textureEntry.ObjectNameString + ".png");
                        }
                    }
                }
                
            }
            matIndex++;
        }

        return output;
    }

    string getLastPart(string inString)
    {
        int pos = inString.LastIndexOf('.');
        return inString.Substring(pos + 1);
    }

    string ExportStaticMesh(string pccPath, string meshName, string umodelPath, string ext, string outputPath, string texturesPath)
    {
        string output = "";
        IMEPackage pcc = MEPackageHandler.OpenMEPackage(pccPath);
        
        List<ExportEntry> staticMeshes = pcc.Exports.Where(exp => exp.ClassName.CaseInsensitiveEquals("StaticMesh")).ToList();
        foreach (ExportEntry entry in staticMeshes)
        {
            if (getLastPart(entry.InstancedFullPath) == meshName)
            {
                var args = new List<string>
                {
                    "-export",
                    $"-" + ext,
                    $"-out=\"{outputPath}\"",
                    entry.FileRef.FilePath,
                    meshName,
                    entry.ClassName
                };

                if (true)
                {
                    var result = Cli.Wrap(umodelPath)
                                    .WithArguments(args)
                                    .WithValidation(CommandResultValidation.None)
                                    .ExecuteAsync();
                }

                var bin = ObjectBinary.From<StaticMesh>(entry);
                output = ExportMaterials(pcc, bin, entry, texturesPath);

                break;
            }
        }

        return output.Length > 0 ? output.Substring(0, output.Length - 1) : "";
    }

    string GeatherActorsInformation(string pccPath)
    {
        string output = "";
        IMEPackage pcc = MEPackageHandler.OpenMEPackage(pccPath);

        List<int> actors = pcc.GetLevelBinary().Actors;
        foreach (int uIndex in actors)
        {
            if (pcc.GetEntry(uIndex) is ExportEntry entry)
            {
                if (entry.ClassName == "StaticMeshActor")
                {
                    ObjectProperty smComp = entry.GetProperty<ObjectProperty>("StaticMeshComponent");
                    if (smComp != null && smComp.Value != 0)
                    {
                        ExportEntry smCompEntry = pcc.GetUExport(smComp.Value);
                        var smProp = smCompEntry.GetProperty<ObjectProperty>("StaticMesh");
                        if (smProp != null)
                        {
                            var smEntry = pcc.GetEntry(smProp.Value);
                            output += getLastPart(smEntry.InstancedFullPath) + "#";
                            Matrix4x4 tfm = ActorUtils.GetLocalToWorld(entry);
                            output += MatrixToString(tfm, '%') + "#";
                        }
                    }
                }
            }
        }

        return output.Length > 0 ? output.Substring(0, output.Length - 1) : "";
    }

    string GetActorBones(string pccPath, string actorName)
    {
        string output = "";

        IMEPackage pcc = MEPackageHandler.OpenMEPackage(pccPath);
        List<ExportEntry> skeletalMeshes = pcc.Exports.Where(exp => exp.ClassName.CaseInsensitiveEquals("SkeletalMesh")).ToList();
        foreach (ExportEntry entry in skeletalMeshes)
        { 
            if (entry.ObjectNameString == actorName)
            {
                SkeletalMesh mesh = ObjectBinary.From<SkeletalMesh>(entry);
                foreach(MeshBone bone in mesh.RefSkeleton)
                {
                    output += bone.Name + "#";
                }

                break;
            }
        }

        return output.Length > 0 ? output.Substring(0, output.Length - 1) : "";
    }

    string GetAnimationsFromPCC(string pccPath)
    {
        StringBuilder sb = new StringBuilder();

        IMEPackage pcc = MEPackageHandler.OpenMEPackage(pccPath);
        List<ExportEntry> animations = pcc.Exports.Where(exp => exp.ClassName.CaseInsensitiveEquals("AnimSequence")).ToList();
        foreach(ExportEntry entry in animations)
        {
            AnimSequence anim = ObjectBinary.From<AnimSequence>(entry);
            anim.DecompressAnimationData();

            string entryPath = entry.InstancedFullPath;
            string[] parts = entryPath.Split('.');

            // write animation name
            // split by $
            sb.Append(parts[parts.Length - 1] + "$");

            List<string> boneNames = anim.Bones;
            // combine output from parts, divided by %-symbol
            for (int i = 0; i < boneNames.Count; i++)
            {
                string boneName = boneNames[i];
                AnimTrack track = anim.RawAnimationData[i];

                // write bone name
                sb.Append(boneName + "#");

                // for each frame we write
                // frame number, position as three numbers and quaternion as four numbers
                // divide numbers by #
                int positionsCount = track.Positions.Count;
                int rotationsCount = track.Rotations.Count;
                int commonPart = Math.Min(positionsCount, rotationsCount);
                for (int j = 0; j < commonPart; j++)
                {
                    sb.Append(j.ToString() + "#");

                    Vector3 pos = track.Positions[j];
                    var quat = track.Rotations[j];
                    sb.Append(pos.X.ToString() + "#");
                    sb.Append(pos.Y.ToString() + "#");
                    sb.Append(pos.Z.ToString() + "#");
                    sb.Append(quat.W.ToString() + "#");
                    sb.Append(quat.X.ToString() + "#");
                    sb.Append(quat.Y.ToString() + "#");
                    sb.Append(quat.Z.ToString() + "#");
                }

                // next for other part
                if (positionsCount > rotationsCount)
                {
                    for (int j = commonPart; j < positionsCount; j++)
                    {
                        sb.Append(j.ToString() + "#");

                        Vector3 pos = track.Positions[j];
                        var quat = track.Rotations[rotationsCount - 1];
                        sb.Append(pos.X.ToString() + "#");
                        sb.Append(pos.Y.ToString() + "#");
                        sb.Append(pos.Z.ToString() + "#");
                        sb.Append(quat.W.ToString() + "#");
                        sb.Append(quat.X.ToString() + "#");
                        sb.Append(quat.Y.ToString() + "#");
                        sb.Append(quat.Z.ToString() + "#");
                    }
                }

                if (rotationsCount > positionsCount)
                {
                    for (int j = commonPart; j < rotationsCount; j++)
                    {
                        sb.Append(j.ToString() + "#");

                        Vector3 pos = track.Positions[positionsCount - 1];
                        var quat = track.Rotations[j];
                        sb.Append(pos.X.ToString() + "#");
                        sb.Append(pos.Y.ToString() + "#");
                        sb.Append(pos.Z.ToString() + "#");
                        sb.Append(quat.W.ToString() + "#");
                        sb.Append(quat.X.ToString() + "#");
                        sb.Append(quat.Y.ToString() + "#");
                        sb.Append(quat.Z.ToString() + "#");
                    }
                }

                // finally devide bone name by symbol %
                sb.Append("%");
            }

            // next start next animation
            // separate by $-symbol
            sb.Append("$");
        }

        string output = sb.ToString();
        return output.Length > 0 ? output.Substring(0, output.Length - 1) : "";
    }

    public void Start(int port)
    {
        _host = WebHost.CreateDefaultBuilder()
            .UseKestrel()
            .Configure(app =>
            {
                app.Map("/api/locations", builder => {
                    builder.Run(async context =>
                    {
                        string pccPath = context.Request.Query["pcc"];
                        await context.Response.WriteAsync(GetLocations(pccPath));
                    });
                });

                app.Map("/api/static", builder => {
                    builder.Run(async context =>
                    {
                        string pccPath = context.Request.Query["pcc"];
                        await context.Response.WriteAsync(GetStaticMeshes(pccPath));
                    });
                });

                app.Map("/api/export", builder => {
                    builder.Run(async context =>
                    {
                        string pccPath = context.Request.Query["pcc"];
                        string meshName = context.Request.Query["name"];
                        string umodelPath = context.Request.Query["umodel"];
                        string ext = context.Request.Query["ext"];
                        string outputPath = context.Request.Query["out"];
                        string texturesPath = context.Request.Query["tex"];
                        await context.Response.WriteAsync(ExportStaticMesh(pccPath, meshName, umodelPath, ext, outputPath, texturesPath));
                    });
                });

                app.Map("/api/actors", builder => {
                    builder.Run(async context =>
                    {
                        string pccPath = context.Request.Query["pcc"];
                        await context.Response.WriteAsync(GeatherActorsInformation(pccPath));
                    });
                });

                app.Map("/api/bones", builder => {
                    builder.Run(async context =>
                    {
                        string pccPath = context.Request.Query["pcc"];
                        string resource = context.Request.Query["res"];
                        await context.Response.WriteAsync(GetActorBones(pccPath, resource));
                    });
                });
                app.Map("/api/animations", builder => {
                    builder.Run(async context =>
                    {
                        string pccPath = context.Request.Query["pcc"];
                        await context.Response.WriteAsync(GetAnimationsFromPCC(pccPath));
                    });
                });
            })
            .UseUrls($"http://localhost:{port}")
            .Build();

        _host.Start();
    }

    public void Stop()
    {
        _host?.StopAsync().Wait();
    }
}

