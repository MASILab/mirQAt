import typer
import numpy as np
import pandas as pd
import pydicom
from pathlib import Path

app = typer.Typer(help="mirQAT: Medical Imaging Research QA Toolkit")


@app.command()
def dcm_instance(dcm_root):
    """
    Check instance numbers in a DICOM folder. Does the instance number match the number of DICOMs in each session?
    Returns (<num1>, <num2>, <num3>)

    Valid: if <num1> == <num2> & <num3> == 0 (<num3> is the diff b/w num1 and num2).
    Invalid: if <num1> != <num2>, i.e. <num3> > 0.
    """
    if Path(dcm_root).exists() == False:
        print("This folder does not exist. Please input an existing folder path.")
    dcm_list = list(Path(dcm_root).glob("**/*.dcm"))
    # dcm_list = glob(os.path.join(dcm_root, "*.dcm"))
    if len(dcm_list) == 0:
        typer.echo(
            "We were unable to find DICOM files in this root directory. Please review path and try again.",
            err=True,
        )
    instanceN = []
    for i in range(len(dcm_list)):
        ds = pydicom.dcmread(str(dcm_list[i]))
        instanceN.append(ds[0x20, 0x13].value)
    # print("max and min of instanceN ", max(instanceN), min(instanceN))
    # typer.secho(f"Max and Min of instanceN is {max(instanceN)} and {min(instanceN)}", fg=typer.colors.GREEN)
    return (
        len(instanceN),
        max(instanceN) - min(instanceN) + 1,
        max(instanceN) - min(instanceN) + 1 - len(instanceN),
    )


@app.command()
def instanceN_fold(
    fold_root,
    save_csv_path: str = typer.Option(
        "instance_num_check.csv", "--output", "-o", show_default=True
    ),
):
    """
    Generates a CSV file comparing instance number, no. of DICOM images.

    Arguments:
        - Root folder
        - Location and name to store CSV output
    Output csv file:
        - instance number using header info
        - if only single folder
        - number of DICOM images for a particular session
        - difference b/w # of DICOM images and Instance number
            - Valid values are those <= 0 (?)
    """
    subj, sess, single_folder, instanceN, dicomN, diff = [], [], [], [], [], []
    subj_list = [x.stem for x in Path(fold_root).iterdir() if x.is_dir()]
    fold_root = Path(fold_root)

    with typer.progressbar(range(0, len(subj_list)), label="Subjects") as subj_prog:
        for i in subj_prog:
            sess_list = [
                x.stem for x in Path(fold_root / subj_list[i]).iterdir() if x.is_dir()
            ]
            subj.extend([subj_list[i]] * len(sess_list))
            sess.extend(sess_list)
            for j in range(len(sess_list)):
                inst_path = [
                    x
                    for x in Path(fold_root / subj_list[i] / sess_list[j]).iterdir()
                    if x.is_dir()
                ]
                instance_list = [x.stem for x in inst_path]
                # set([x.parent.parts[-1] for x in Path(p / subj_list[i] / sess_list[j]).rglob("*.dcm")])
                if len(instance_list) == 1:
                    single_folder.append(1)
                else:
                    single_folder.append(0)
                # inst_path = [Path(p / subj_list[i] / sess_list[j] / x) for x in instance_list]
                max_index = np.argmax([len(list(p.glob("*.dcm"))) for p in inst_path])
                # print(max_index, inst_path[max_index])
                if "new_max" in [
                    p.stem
                    for p in Path(fold_root / subj_list[i] / sess_list[j]).iterdir()
                ]:
                    typer.echo(
                        f"A folder is already called 'new_max' for Subject {subj_list[i]}. You may have run this command before. Please review for discrepancies.\n",
                        err=True,
                    )
                else:
                    (inst_path[max_index]).rename(
                        fold_root / subj_list[i] / sess_list[j] / "new_max"
                    )

                try:
                    inst_n, dicom_n, same = dcm_instance(
                        fold_root / subj_list[i] / sess_list[j] / "new_max"
                    )
                    instanceN.append(inst_n)
                    dicomN.append(dicom_n)
                    diff.append(same)
                except:
                    instanceN.append("")
                    dicomN.append("")
                    diff.append("")
                    typer.echo(
                        f"An error occurred while trying to perform instance number checking for Subject {subj_list[i]}.\n",
                        err=True,
                    )

    # assert len(subj) == len(sess) == len(single_folder)

    col_names = [
        "subject",
        "session",
        "single_folder",
        "instanceN",
        "dicomN",
        "dicomN-instanceN",
    ]
    data = pd.DataFrame(
        zip(subj, sess, single_folder, instanceN, dicomN, diff), columns=col_names
    )
    data.to_csv(save_csv_path, index=False)
    typer.secho(
        f"Instance number checking complete! Please review output in file: {str(save_csv_path)}.",
        fg=typer.colors.GREEN,
    )


@app.command()
def dcm_slicedistance(dcm_root):
    """
    Calculate slice distance given a directory or subdirectories with DICOM images.
    """
    if Path(dcm_root).exists() == False:
        print("This folder does not exist. Please input an existing folder path.")
    dcm_list = list(Path(dcm_root).glob("**/*.dcm"))
    # dcm_list = os.listdir(dcm_root)
    # dcm_list = glob(os.path.join(dcm_root, "*.dcm"))
    ds_list = []
    # skipped_accession = []
    for i in range(len(dcm_list)):
        # ds = pydicom.dcmread(dcm_list[i])
        ds = pydicom.dcmread(str(dcm_list[i]))
        if hasattr(ds, "SliceLocation"):  # some images do not have 'SliceLocation'
            ds_list.append(ds.SliceLocation)
    #       else:
    #           skipped_accession.append(ds.AccessionNumber)

    #   print(f'The following accession numbers have missing "SliceLocation": {Counter(skipped_accession)}.')
    ds_sort = sorted(ds_list, reverse=True)
    res = 1
    for i in range(0, len(ds_sort) - 2):
        # print((ds_sort[i] - ds_sort[i + 1]), (ds_sort[i + 1] - ds_sort[i + 2]))
        if not abs(
            (ds_sort[i] - ds_sort[i + 1]) - (ds_sort[i + 1] - ds_sort[i + 2])
        ) < (ds_sort[0] - ds_sort[1]):
            res = 0
    return res


@app.command()
def sliceDis_fold(fold_root, save_csv_path="slice_dist_check.csv"):
    """
    Generates a csv file with DICOM slice distance information.

    Arguments:
        - Root folder
        - Location and name to store CSV output
    Output csv file:
        - Instance number
        - If only one instance: single folder = 1 or 0 otherwise
        - distance_check: Output of `dcm_slicedistance` function calculated for each session
    """
    subj_list = [x.stem for x in Path(fold_root).iterdir() if x.is_dir()]
    sess, single_folder, diff = [], [], []
    with typer.progressbar(range(0, len(subj_list)), label="Subjects") as subj_prog:
        for i in subj_prog:
            # if i > 3: break
            subj_path = Path(fold_root) / subj_list[i]
            sess_list = [x.stem for x in Path(subj_path).iterdir() if x.is_dir()]
            for j in range(len(sess_list)):
                sess.append(sess_list[j])
                # print("(i, j): ", i, j, sess_list[j])
                sess_path = subj_path / sess_list[j]
                instance_list = [
                    x.stem for x in Path(sess_path).iterdir() if x.is_dir()
                ]
                if len(instance_list) == 1:
                    single_folder.append(1)
                else:
                    single_folder.append(0)
                try:
                    # same = dcm_slicedistance(sess_path + "/new_max/DICOM") # the DICOM files are under `new_max` and not `new_max/DICOM`
                    same = dcm_slicedistance(sess_path / "new_max")
                    diff.append(same)
                except:
                    try:
                        same = dcm_slicedistance(sess_path / "file0/DICOM")
                        diff.append(same)
                    except:
                        diff.append("")

                        print("dicom error")
    data = pd.DataFrame()
    data["sess"] = sess
    data["single_folder"] = single_folder
    data["distance_check"] = diff
    data.to_csv(save_csv_path, index=False)
    typer.secho(
        f"Slice distance check complete! Please review output in file: {str(save_csv_path)}.",
        fg=typer.colors.GREEN,
    )


@app.command()
def filter_few_slices(csv_path="instance_num_check.csv"):
    """
    Filter to exclude sessions with few slices (less than 20) but that pass instance number check (dicomN - instanceN > 0).
    
    TODO: should we allow the thresholds to be user-definable parameters.
    """
    df = pd.read_csv(csv_path)
    auto_QA_result = []
    for i, item in df.iterrows():
        if item["dicomN-instanceN"] > 0 or item["instanceN"] < 20:
            auto_QA_result.append("bad")
        else:
            auto_QA_result.append("good")
    df["auto"] = auto_QA_result
    df.to_csv(csv_path, index=False)
    typer.secho(
        "Filtering completed. Review instance number check CSV file for updated output.",
        fg=typer.colors.GREEN,
    )
