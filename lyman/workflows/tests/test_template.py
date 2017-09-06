import nipype

from ..template import (define_template_workflow,
                        TemplateInput,
                        AnatomicalSegmentation,
                        TemplateReport)


class TestTemplateWorkflow(object):

    def test_template_workflow_creation(self, lyman_info):

        proj_info = lyman_info["proj_info"]
        subjects = lyman_info["subjects"]

        wf = define_template_workflow(
            proj_info, subjects
        )

        # Check basic information about the workflow
        assert isinstance(wf, nipype.Workflow)
        assert wf.name == "template"
        assert wf.base_dir == proj_info.cache_dir

        # Check root directory of output
        template_out = wf.get_node("template_output")
        assert template_out.inputs.base_directory == proj_info.analysis_dir

        # Check the list of nodes we expect
        expected_nodes = ["subject_source", "template_input",
                          "crop_image", "zoom_image", "reorient_image",
                          "generate_reg", "invert_reg",
                          "transform_wmparc", "anat_segment",
                          "hemi_source", "tag_surf", "combine_hemis",
                          "template_qc", "template_output"]
        expected_nodes.sort()
        assert wf.list_node_names() == expected_nodes

        # Check iterables
        subject_source = wf.get_node("subject_source")
        assert subject_source.iterables == ("subject", subjects)

    def test_template_input(self, freesurfer):

        res = TemplateInput(
            data_dir=freesurfer["data_dir"],
            subject=freesurfer["subject"]
        ).run()

        assert res.outputs.norm_file == freesurfer["norm_file"]
        assert res.outputs.wmparc_file == freesurfer["wmparc_file"]

        output_path = "{}/template".format(freesurfer["subject"])
        assert res.outputs.output_path == output_path

    def test_anatomical_segmentation(self, execdir, freesurfer):

        res = AnatomicalSegmentation(
            wmparc_file=freesurfer["wmparc_file"],
        ).run()

        assert res.outputs.seg_file == execdir.join("seg.nii.gz")
        assert res.outputs.mask_file == execdir.join("mask.nii.gz")

    def test_template_report(self, execdir, template):

        res = TemplateReport(
            seg_file=template["seg_file"],
            mask_file=template["mask_file"],
            surf_file=template["surf_file"],
            anat_file=template["anat_file"],
        ).run()

        assert res.outputs.seg_plot == execdir.join("seg.png")
        assert res.outputs.mask_plot == execdir.join("mask.png")
        assert res.outputs.surf_plot == execdir.join("surf.png")
        assert res.outputs.anat_plot == execdir.join("anat.png")
