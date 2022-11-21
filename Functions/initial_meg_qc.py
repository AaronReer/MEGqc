import os
import mne
import configparser

def make_folders_meg(sid: str):
    '''Create folders (if they dont exist yet). 
    NOT USED ANY MORE, LEFT IN CASE NEEDED LATER

    Folders are created in BIDS-compliant directory order: 
    Working directory - Subject - derivtaives - megQC - csvs and figures

    Args:
    sid (int): subject Id, must be a string, like '1'. '''


    #Make sure to add subfolders on the list here AFTER the parent folder.
    path_list = [f'../derivatives', 
    f'../derivatives/sub-{sid}',
    f'../derivatives/sub-{sid}/megqc',
    f'../derivatives/sub-{sid}/megqc/csv files',
    f'../derivatives/sub-{sid}/megqc/figures',
    f'../derivatives/sub-{sid}/megqc/reports']

    for path in path_list:
        if os.path.isdir(path)==False: #if directory doesnt exist yet - create
            os.mkdir(path)



def get_all_config_params(config_file_name: str):
    '''Parse all the parameters from config and put into a python dictionary 
    divided by sections. Parsing approach can be changed here, which 
    will not affect working of other fucntions.
    
    Return:
    all_qc_params: dictionary of dictionaries, where each one refers to 
    a QC pipeline section and contains corresponding parameters.
    '''
    
    all_qc_params = {}

    config = configparser.ConfigParser()
    config.read(config_file_name)

    default_section = config['DEFAULT']

    m_or_g_chosen = default_section['do_for'] 
    m_or_g_chosen = m_or_g_chosen.replace(" ", "")
    m_or_g_chosen = m_or_g_chosen.split(",")

    dataset_path = default_section['data_directory']
    tmin = default_section['data_crop_tmin']
    tmax = default_section['data_crop_tmax']

    if not tmin: 
        tmin = 0
    else:
        tmin=float(tmin)
    if not tmax: 
        tmax = None
    else:
        tmax=float(tmax)

    default_params = dict({
        'm_or_g_chosen': m_or_g_chosen, 
        'dataset_path': dataset_path,
        'crop_tmin': tmin,
        'crop_tmax': tmax})
    all_qc_params['default'] = default_params

    filtering_section = config['Filtering']
    if filtering_section['apply_filtering'] is True:
        filtering_params = dict({
            'l_freq': filtering_section.getfloat('l_freq'),
            'h_freq': filtering_section.getfloat('h_freq'),
            'method': filtering_section['method']})
        all_qc_params['Filtering'] = filtering_params
    else: 
        all_qc_params['Filtering'] = 'Not apply'


    epoching_section = config['Epoching']
    stim_channel = epoching_section['stim_channel'] 
    stim_channel = stim_channel.replace(" ", "")
    stim_channel = stim_channel.split(",")
    if stim_channel==['']:
        stim_channel=None

    epoching_params = dict({
    'event_dur': epoching_section.getfloat('event_dur'),
    'epoch_tmin': epoching_section.getfloat('epoch_tmin'),
    'epoch_tmax': epoching_section.getfloat('epoch_tmax'),
    'stim_channel': stim_channel})
    all_qc_params['Epoching'] = epoching_params


    rmse_section = config['RMSE']
    std_lvl = rmse_section.getint('std_lvl')
    all_qc_params['RMSE'] = dict({'std_lvl':  std_lvl})
    

    psd_section = config['PSD']
    psd_params = dict({
    'freq_min': psd_section.getfloat('freq_min'),
    'freq_max': psd_section.getfloat('freq_max'),
    'mean_power_per_band_needed': psd_section.getboolean('mean_power_per_band_needed'),
    'n_fft': psd_section.getint('n_fft'),
    'n_per_seg': psd_section.getint('n_per_seg')})
    all_qc_params['PSD'] = psd_params


    ptp_manual_section = config['PTP_manual']
    ptp_manual_params = dict({
    'pair_dist_sec': ptp_manual_section.getfloat('pair_dist_sec'),
    'thresh_lvl': ptp_manual_section.getfloat('ptp_thresh_lvl')})
    all_qc_params['PTP_manual'] = ptp_manual_params


    ptp_mne_section = config['PTP_auto']
    ptp_auto_params = dict({
    'peak_m': ptp_mne_section.getfloat('peak_m'),
    'flat_m': ptp_mne_section.getfloat('flat_m'),
    'peak_g': ptp_mne_section.getfloat('peak_g'),
    'flat_g': ptp_mne_section.getfloat('flat_g'),
    'bad_percent': ptp_mne_section.getint('bad_percent'),
    'min_duration': ptp_mne_section.getfloat('min_duration')})
    all_qc_params['PTP_auto'] = ptp_auto_params


    ecg_section = config['ECG']
    ecg_params = dict({})
    all_qc_params['ECG'] = ecg_params

    eog_section = config['EOG']
    eog_params = dict({})
    all_qc_params['EOG'] = eog_params

    head_section = config['Head_movement']
    head_params = dict({})
    all_qc_params['Head'] = head_params

    muscle_section = config['Muscle']
    muscle_params = dict({})
    all_qc_params['Muscle'] = muscle_params

    return all_qc_params


def Epoch_meg(epoching_params, data: mne.io.Raw):

    '''Gives epoched data in 2 separated data frames: mags and grads + as epoch objects.
    
    Args:
    config
    data (mne.io.Raw): data in raw format
    
    Returns: 
    n_events (int): number of events(=number of epochs)
    df_epochs_mags (pd. Dataframe): data frame containing data for all epochs for mags 
    df_epochs_grads (pd. Dataframe): data frame containing data for all epochs for grads 
    epochs_mags (mne. Epochs): epochs as mne data structure for magnetometers
    epochs_grads (mne. Epochs): epochs as mne data structure for gradiometers '''

    event_dur = epoching_params['event_dur']
    epoch_tmin = epoching_params['epoch_tmin']
    epoch_tmax = epoching_params['epoch_tmax']
    stim_channel = epoching_params['stim_channel']

    if stim_channel is None:
        picks_stim = mne.pick_types(data.info, stim=True)
        stim_channel = []
        for ch in picks_stim:
            stim_channel.append(data.info['chs'][ch]['ch_name'])
    print('Stimulus channels detected:', stim_channel)

    picks_magn = data.copy().pick_types(meg='mag').ch_names if 'mag' in data else None
    picks_grad = data.copy().pick_types(meg='grad').ch_names if 'grad' in data else None

    events = mne.find_events(data, stim_channel=stim_channel, min_duration=event_dur)
    n_events=len(events)

    if n_events == 0:
        print('No events with set minimum duration were found using all stimulus channels. No epoching can be done. Try different event duration in config file.')
        dict_of_dfs_epoch = {
        'grads': None,
        'mags': None}

        epochs_mg = {
        'grads': None,
        'mags': None}
        return dict_of_dfs_epoch, epochs_mg

    epochs_mags = mne.Epochs(data, events, picks=picks_magn, tmin=epoch_tmin, tmax=epoch_tmax, preload=True, baseline = None)
    epochs_grads = mne.Epochs(data, events, picks=picks_grad, tmin=epoch_tmin, tmax=epoch_tmax, preload=True, baseline = None)

    df_epochs_mags = epochs_mags.to_data_frame(time_format=None, scalings=dict(mag=1, grad=1))
    df_epochs_grads = epochs_grads.to_data_frame(time_format=None, scalings=dict(mag=1, grad=1))

    dict_of_dfs_epoch = {
    'grads': df_epochs_grads,
    'mags': df_epochs_mags}

    epochs_mg = {
    'grads': epochs_grads,
    'mags': epochs_mags}

    return dict_of_dfs_epoch, epochs_mg

def initial_processing(default_settings: dict, filtering_settings: dict, epoching_params:dict, data_file: str):

    '''Here all the initial actions need to work with MEG data are done: 
    - load fif file and convert into raw,
    - create folders in BIDS compliant format,
    - crop the data if needed,
    - filter and downsample the data,
    - epoch the data.

    Args:
    config: config file like settings.ini
    data_file (str): path to the data file

    Returns: 
    dict_of_dfs_epoch (dict with 2 pd. Dataframe): 2 data frames containing data for all epochs for mags and grads
    epochs_mg (dict with 2 mne. Epochs): 2 epoch objects for mags and  grads
    channels (dict): mags and grads channels names
    raw_bandpass(mne.raw): data only filtered, cropped (*)
    raw_bandpass_resamp(mne.raw): data filtered and resampled, cropped (*)
    raw_cropped(mne.io.Raw): data in raw format, cropped, not filtered, not resampled (*)
    raw(mne.io.Raw): original data in raw format, not cropped, not filtered, not resampled.
    (*): if duration was set to None - the data will not be cropped and these outputs 
    will return what is stated, but in origibal duration.
    '''

    active_shielding_used = False
    try:
        raw = mne.io.read_raw_fif(data_file, on_split_missing='ignore')
    except: 
        raw = mne.io.read_raw_fif(data_file, allow_maxshield=True, on_split_missing='ignore')
        active_shielding_used = True

    mag_ch_names = raw.copy().pick_types(meg='mag').ch_names if 'mag' in raw else None
    grad_ch_names = raw.copy().pick_types(meg='grad').ch_names if 'grad' in raw else None
    channels = {'mags': mag_ch_names, 'grads': grad_ch_names}

    #crop the data to calculate faster:
    tmax=default_settings['crop_tmax']
    if tmax is None: 
        tmax = raw.times[-1] 
    raw_cropped = raw.copy().crop(tmin=default_settings['crop_tmin'], tmax=tmax)

    #Data filtering:
    raw_filtered = raw_cropped.copy()
    if filtering_settings != 'Not apply':
        raw_cropped.load_data(verbose=True) #Data has to be loaded into mememory before filetering:
        raw_filtered = raw_cropped.copy()
        raw_filtered.filter(l_freq=filtering_settings['lfreq'], h_freq=filtering_settings['h_freq'], picks='meg', method=filtering_settings['method'], iir_params=None)
        
        #And downsample:
        raw_filtered_resampled = raw_filtered.copy().resample(sfreq=filtering_settings['h_freq']*5)
        #frequency to resample is 5 times higher than the maximum chosen frequency of the function
    else:
        raw_filtered_resampled = raw_filtered.copy()
        #OR maybe we dont need these 2 copies of data at all? Think how to get rid of them, 
        # because they are used later. Referencing might mess up things, check that.
    

    #Apply epoching: USE NON RESAMPLED DATA. Or should we resample after epoching? 
    # Since sampling freq is 1kHz and resampling is 500Hz, it s not that much of a win...

    dict_of_dfs_epoch, epochs_mg = Epoch_meg(epoching_params, data=raw_filtered)

    return dict_of_dfs_epoch, epochs_mg, channels, raw_filtered, raw_filtered_resampled, raw_cropped, raw, active_shielding_used



def sanity_check(m_or_g_chosen, channels):
    '''Check if the channels which the user gave in config file to analize actually present in the data set'''

    if m_or_g_chosen != ['mags'] and m_or_g_chosen != ['grads'] and m_or_g_chosen != ['mags', 'grads']:
        m_or_g_chosen = []
    if channels['mags'] is None and 'mags' in m_or_g_chosen:
        print('There are no magnetometers in this data set: check parameter do_for in config file. Analysis will be done only for gradiometers.')
        m_or_g_chosen.remove('mags')
    elif channels['grads'] is None and 'grads' in m_or_g_chosen:
        print('There are no gradiometers in this data set: check parameter do_for in config file. Analysis will be done only for magnetometers.')
        m_or_g_chosen.remove('grads')
    elif channels['mags'] is None and channels['grads'] is None:
        print ('There are no magnetometers or gradiometers in this data set. Analysis will not be done.')
        m_or_g_chosen = []
    return m_or_g_chosen