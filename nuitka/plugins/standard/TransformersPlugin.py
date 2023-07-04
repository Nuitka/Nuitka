#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Plugin to provide transformers implicit dependencies.

"""


from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginTransformers(NuitkaPluginBase):
    plugin_name = "transformers"

    plugin_desc = "Provide implicit imports for transformers package."

    @staticmethod
    def isAlwaysEnabled():
        return True

    # Found via grep -re "_import_structure = {"
    _import_structure_modules = (
        "transformers",
        "transformers.generation",
        "transformers.models.albert",
        "transformers.models.align",
        "transformers.models.altclip",
        "transformers.models.audio_spectrogram_transformer",
        "transformers.models.auto",
        "transformers.models.bart",
        "transformers.models.barthez",
        "transformers.models.bartpho",
        "transformers.models.beit",
        "transformers.models.bert",
        "transformers.models.bertweet",
        "transformers.models.bert_generation",
        "transformers.models.bert_japanese",
        "transformers.models.bigbird_pegasus",
        "transformers.models.big_bird",
        "transformers.models.biogpt",
        "transformers.models.bit",
        "transformers.models.blenderbot",
        "transformers.models.blenderbot_small",
        "transformers.models.blip",
        "transformers.models.blip_2",
        "transformers.models.bloom",
        "transformers.models.bridgetower",
        "transformers.models.byt5",
        "transformers.models.camembert",
        "transformers.models.canine",
        "transformers.models.chinese_clip",
        "transformers.models.clap",
        "transformers.models.clip",
        "transformers.models.clipseg",
        "transformers.models.codegen",
        "transformers.models.conditional_detr",
        "transformers.models.convbert",
        "transformers.models.convnext",
        "transformers.models.convnextv2",
        "transformers.models.cpm",
        "transformers.models.cpmant",
        "transformers.models.ctrl",
        "transformers.models.cvt",
        "transformers.models.data2vec",
        "transformers.models.deberta",
        "transformers.models.deberta_v2",
        "transformers.models.decision_transformer",
        "transformers.models.deformable_detr",
        "transformers.models.deit",
        "transformers.models.deta",
        "transformers.models.detr",
        "transformers.models.dinat",
        "transformers.models.distilbert",
        "transformers.models.donut",
        "transformers.models.dpr",
        "transformers.models.dpt",
        "transformers.models.efficientformer",
        "transformers.models.efficientnet",
        "transformers.models.electra",
        "transformers.models.encoder_decoder",
        "transformers.models.ernie",
        "transformers.models.ernie_m",
        "transformers.models.esm",
        "transformers.models.flaubert",
        "transformers.models.flava",
        "transformers.models.fnet",
        "transformers.models.focalnet",
        "transformers.models.fsmt",
        "transformers.models.funnel",
        "transformers.models.git",
        "transformers.models.glpn",
        "transformers.models.gpt2",
        "transformers.models.gptj",
        "transformers.models.gptsan_japanese",
        "transformers.models.gpt_bigcode",
        "transformers.models.gpt_neo",
        "transformers.models.gpt_neox",
        "transformers.models.gpt_neox_japanese",
        "transformers.models.gpt_sw3",
        "transformers.models.graphormer",
        "transformers.models.groupvit",
        "transformers.models.herbert",
        "transformers.models.hubert",
        "transformers.models.ibert",
        "transformers.models.imagegpt",
        "transformers.models.informer",
        "transformers.models.jukebox",
        "transformers.models.layoutlm",
        "transformers.models.layoutlmv2",
        "transformers.models.layoutlmv3",
        "transformers.models.layoutxlm",
        "transformers.models.led",
        "transformers.models.levit",
        "transformers.models.lilt",
        "transformers.models.llama",
        "transformers.models.longformer",
        "transformers.models.longt5",
        "transformers.models.luke",
        "transformers.models.lxmert",
        "transformers.models.m2m_100",
        "transformers.models.marian",
        "transformers.models.markuplm",
        "transformers.models.mask2former",
        "transformers.models.maskformer",
        "transformers.models.mbart",
        "transformers.models.mbart50",
        "transformers.models.mctct",
        "transformers.models.mega",
        "transformers.models.megatron_bert",
        "transformers.models.mgp_str",
        "transformers.models.mluke",
        "transformers.models.mmbt",
        "transformers.models.mobilebert",
        "transformers.models.mobilenet_v1",
        "transformers.models.mobilenet_v2",
        "transformers.models.mobilevit",
        "transformers.models.mpnet",
        "transformers.models.mt5",
        "transformers.models.mvp",
        "transformers.models.nat",
        "transformers.models.nezha",
        "transformers.models.nllb",
        "transformers.models.nllb_moe",
        "transformers.models.nystromformer",
        "transformers.models.oneformer",
        "transformers.models.openai",
        "transformers.models.open_llama",
        "transformers.models.opt",
        "transformers.models.owlvit",
        "transformers.models.pegasus",
        "transformers.models.pegasus_x",
        "transformers.models.perceiver",
        "transformers.models.phobert",
        "transformers.models.pix2struct",
        "transformers.models.plbart",
        "transformers.models.poolformer",
        "transformers.models.prophetnet",
        "transformers.models.qdqbert",
        "transformers.models.rag",
        "transformers.models.realm",
        "transformers.models.reformer",
        "transformers.models.regnet",
        "transformers.models.rembert",
        "transformers.models.resnet",
        "transformers.models.retribert",
        "transformers.models.roberta",
        "transformers.models.roberta_prelayernorm",
        "transformers.models.roc_bert",
        "transformers.models.roformer",
        "transformers.models.rwkv",
        "transformers.models.sam",
        "transformers.models.segformer",
        "transformers.models.sew",
        "transformers.models.sew_d",
        "transformers.models.speecht5",
        "transformers.models.speech_encoder_decoder",
        "transformers.models.speech_to_text",
        "transformers.models.speech_to_text_2",
        "transformers.models.splinter",
        "transformers.models.squeezebert",
        "transformers.models.swin",
        "transformers.models.swin2sr",
        "transformers.models.swinv2",
        "transformers.models.switch_transformers",
        "transformers.models.t5",
        "transformers.models.table_transformer",
        "transformers.models.tapas",
        "transformers.models.tapex",
        "transformers.models.timesformer",
        "transformers.models.time_series_transformer",
        "transformers.models.trajectory_transformer",
        "transformers.models.transfo_xl",
        "transformers.models.trocr",
        "transformers.models.tvlt",
        "transformers.models.unispeech",
        "transformers.models.unispeech_sat",
        "transformers.models.upernet",
        "transformers.models.van",
        "transformers.models.videomae",
        "transformers.models.vilt",
        "transformers.models.vision_encoder_decoder",
        "transformers.models.vision_text_dual_encoder",
        "transformers.models.visual_bert",
        "transformers.models.vit",
        "transformers.models.vit_hybrid",
        "transformers.models.vit_mae",
        "transformers.models.vit_msn",
        "transformers.models.wav2vec2",
        "transformers.models.wav2vec2_conformer",
        "transformers.models.wav2vec2_phoneme",
        "transformers.models.wav2vec2_with_lm",
        "transformers.models.wavlm",
        "transformers.models.whisper",
        "transformers.models.xglm",
        "transformers.models.xlm",
        "transformers.models.xlm_prophetnet",
        "transformers.models.xlm_roberta",
        "transformers.models.xlm_roberta_xl",
        "transformers.models.xlnet",
        "transformers.models.xmod",
        "transformers.models.x_clip",
        "transformers.models.yolos",
        "transformers.models.yoso",
        "transformers.onnx",
        "transformers.tools",
    )

    def getImplicitImports(self, module):
        full_name = module.getFullName()

        if full_name in self._import_structure_modules:
            for sub_module_name in self.queryRuntimeInformationSingle(
                setup_codes="import %s" % full_name.asString(),
                value="list(%s._import_structure.keys())" % full_name.asString(),
                info_name="import_structure_for_%s"
                % full_name.asString().replace(".", "_"),
            ):
                sub_module_name = full_name.getChildNamed(sub_module_name)

                if (
                    sub_module_name == "transformers.testing_utils"
                    and not self.evaluateCondition(
                        full_name="transformers", condition="use_pytest"
                    )
                ):
                    continue

                yield sub_module_name
