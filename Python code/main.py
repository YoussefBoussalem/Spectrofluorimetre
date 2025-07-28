import os
from time import sleep
import yaml
from monochromator import MonochromatorA, MonochromatorB
from waveLength import WaveLength, WLRange
from slit import Slit
from measure import EmScanMeasure, ExScanMeasure, synchroScanMeasure, uniqueWLMeasure
from integrationTime import IntegrationTime


# Si le programme est exécuté depuis le script Python
application_path = os.path.dirname(os.path.abspath(__file__))


def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def print_yaml_content(file_path):
    content = read_yaml(file_path)
    print(yaml.dump(content, default_flow_style=False))
    
def createConfiguredMonochromators(config):
    """
    Create monochromator objects (A or B) for excitation and emission based on config dict.
    Returns a dict: {'excitation': ..., 'emission': ...}
    """
    monos = {}
    for mono_key in ['excitation monochromator', 'emission monochromator']:
        mono_conf = config.get(mono_key, {})
        mono_type = mono_conf.get('type', 'A')
        offset = mono_conf.get('offset', 0)
        coeff = mono_conf.get('coeff', 1.0)
        port = mono_conf.get('serial port')
        baud = mono_conf.get('serial baud rate', 9600)
        min_step = mono_conf.get('min step count', 0)
        max_step = mono_conf.get('max step count', 10000)
        wLValue = WaveLength(0)
        wLOffset = WaveLength(offset)
        is_ex = mono_key == 'excitation monochromator'
        is_em = mono_key == 'emission monochromator'

        if mono_type == 'A':
            mono = MonochromatorA(
                wLValue, wLOffset, coeff, port, baud, 0, min_step, max_step, em=is_em, ex=is_ex
            )
        elif mono_type == 'B':
            # For B, get phase and slits if present
            phase = mono_conf.get('phase coeff')

            slits_conf = mono_conf.get('SLITS')
            slit_number = slits_conf.get('number of slits', 1)
            slit_offset = slits_conf.get('offset')
            slit_coeff = slits_conf.get('coeff')
            slit_min = slits_conf.get('min step count')
            slit_max = slits_conf.get('max step count')
            # Use the same serial port as the monochromator for the slit
            slits = Slit(
                numberOfSlits=slit_number, value=WaveLength(0), offsetWL=WaveLength(slit_offset), 
                coefWL=slit_coeff, step=0, minStep=slit_min, maxStep=slit_max
            )
            mono = MonochromatorB(
                wLValue, wLOffset, coeff, phase, slits, port, baud, 0, min_step, max_step, em=is_em, ex=is_ex
            )
        else:
            raise ValueError(f"Unknown monochromator type: {mono_type}")
        monos[mono_key] = mono
    return monos

def createMesurements(monochromators, measurements_config):
    # returns dictionnary of the measurements inside the yaml config measurements_config
    measures = {}

    scans = measurements_config.get('scans', [])
    for scan in scans:
        name = scan.get('name', 'Unnamed Scan')
        scan_type = scan.get('type', '').lower()
        params = scan.get('parameters', {})

        # Parse integration time
        integration_time_str = str(params.get('integration time', '100ms')).replace('ms', '')
        integration_time = IntegrationTime(int(float(integration_time_str)))

        # Parse resolution
        resolution = params.get('resolution', 0.1)

        # Parse scan range if present
        scan_range = params.get('scan range', {})
        start = scan_range.get('start')
        end = scan_range.get('end')
        step = scan_range.get('step size', 1)

        # Parse wavelengths
        ex_wl = params.get('excitation wavelength')
        em_wl = params.get('emission wavelength')
        offset_wl = params.get('offset wavelength')

        # Select monochromators
        ex_mono = monochromators.get('excitation monochromator')
        em_mono = monochromators.get('emission monochromator')

        # Instantiate the correct Measure class
        if scan_type == 'emission':
            # Emission scan: excitation wavelength fixed, emission range scanned
            wl_range = WLRange(WaveLength(start), WaveLength(end), WaveLength(step))
            measure = EmScanMeasure(name, wl_range, WaveLength(ex_wl), integration_time, ex_mono, em_mono, resolution)
        elif scan_type == 'excitation':
            # Excitation scan: emission wavelength fixed, excitation range scanned
            wl_range = WLRange(WaveLength(start), WaveLength(end), WaveLength(step))
            measure = ExScanMeasure(name, WaveLength(em_wl), wl_range, integration_time, ex_mono, em_mono, resolution)
        elif scan_type == 'synchronous':
            # Synchronous scan: scan excitation range, emission = excitation + offset
            wl_range = WLRange(WaveLength(start), WaveLength(end), WaveLength(step))
            measure = synchroScanMeasure(name, WaveLength(offset_wl), wl_range, integration_time, ex_mono, em_mono, resolution)
        elif scan_type == 'singular':
            # Single point measurement
            measure = uniqueWLMeasure(name, WaveLength(em_wl), WaveLength(ex_wl), integration_time, ex_mono, em_mono, resolution)
        else:
            print(f"Unknown scan type: {scan_type} in scan {name}")
            continue

        measures[name] = measure

    return measures

def interactive_run():
    print("Spectrofluorimeter Interactive Command Line")
    print("="*70)

    # 1. Create monochromator objects
    config_path = os.path.join(application_path, 'SYSTEM_CONFIG/systemA_config.yml') 
    config = read_yaml(config_path)
    monochromators = createConfiguredMonochromators(config)
    print("Monochromator objects created.")

    # 2. Ask user for motor initialization
    init_choice = input("Initialize motors? (yes/no): ").strip().lower()
    if init_choice == "yes":
        for key, mono in monochromators.items():
            print(f"Initializing motors for {key}...")
            mono.initMotors()
            print(f"{key} initialized.")
    else:
        print("WARNING: Running without initialization may damage the motors!")

    # 3. List YAML files in Measure Config folder
    measure_folder = os.path.join(application_path, 'Measure Config')
    files = [f for f in os.listdir(measure_folder) if f.endswith('.yml') or f.endswith('.yaml')]
    print("\nAvailable measurement config files:")
    for idx, fname in enumerate(files):
        print(f"{idx+1}: {fname}")

    # 4. Ask user to choose file by number
    while True:
        try:
            file_choice = int(input("Choose a file by number: "))
            if 1 <= file_choice <= len(files):
                chosen_file = files[file_choice-1]
                break
            else:
                print("Invalid choice. Please choose a number from the list.")
        except Exception:
            print("Invalid input. Enter a number.")

    measurements_config = read_yaml(os.path.join(measure_folder, chosen_file))

    # 5. Create measure objects
    measures = createMesurements(monochromators, measurements_config)
    print(f"\n{len(measures)} measurement(s) created:")
    for idx, (name, measure) in enumerate(measures.items(), 1):
        print(f"{idx}. {name} ({measure.__class__.__name__})")
        print(measure)
        print("-"*50)

    # 6. Print min/max wavelength and resolution info
    for key, mono in monochromators.items():
        min_wl = mono.getWaveLengthFromStep(mono.minWLStep)
        max_wl = mono.getWaveLengthFromStep(mono.maxWLStep)
        print(f"{key}: Min WL = {min_wl.value} nm, Max WL = {max_wl.value} nm")
        if isinstance(mono, MonochromatorB):
            print(f"Resolution range: {mono.slits.offsetWL.value} to {mono.slits.offsetWL.value + mono.slits.coefWL * mono.slits.maxStep}")

    # 7. Confirm everything is correct
    confirm = input("Does everything look correct? (yes/no): ").strip().lower()
    if confirm == "no":
        print("Cancelling. Returning to file selection.")
        return interactive_run()
    elif confirm != "yes":
        print("Invalid input. Exiting.")
        return interactive_run()

    # 8. Run measurements in order
    for idx, (name, measure) in enumerate(measures.items(), 1):
        print(f"\nRunning measurement {idx}: {name} ({measure.__class__.__name__})")
        print(measure)
        measure.measure()
        measure.saveResults(os.path.join(application_path, "Measure CSV"))
        print(f"Measurement {name} complete.")
        print("-"*70)

interactive_run()