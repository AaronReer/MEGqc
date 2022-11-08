import mne

def EOG_meg_qc(config, raw: mne.io.Raw, m_or_g_chosen: list):
    """Main psd function"""

    #eog_section = config['EOG']

    picks_EOG = mne.pick_types(raw.info, eog=True)
    if picks_EOG.size == 0:
        print('No EOG channels found is this data set - EOG artifacts can not br detected')
        return
    # else:
    #     EOG_channel_name=[]
    #     for i in range(0,len(picks_EOG)):
    #         EOG_channel_name.append(raw.info['chs'][picks_EOG[i]]['ch_name'])
    #     print('EOG channels found: ', EOG_channel_name)
    # eog_events=mne.preprocessing.find_eog_events(raw, thresh=None, ch_name=EOG_channel_name)
    eog_events=mne.preprocessing.find_eog_events(raw, thresh=None, ch_name=None)

    # ch_name: This doesn’t have to be a channel of eog type; it could, for example, also be an ordinary 
    # EEG channel that was placed close to the eyes, like Fp1 or Fp2.
    #or just use none as channel, so the eog will be found automatically

    eog_events_times  = (eog_events[:, 0] - raw.first_samp) / raw.info['sfreq']

    #WHAT SHOULD WE SHOW? CAN PLOT THE EOG CHANNEL. OR EOG EVENTS ON TOP OF 1 OF THE CHANNELS DATA. OR ON EVERY CHANNELS DATA?

    eog_epochs = mne.preprocessing.create_eog_epochs(raw, baseline=(-0.5, -0.2))

    list_of_desc = []
    list_of_figs = []
    list_of_figs_ecg_sensors = []
    list_of_desc_fig_ecg_sensors = []

    for m_or_g  in m_or_g_chosen:
        list_of_figs.append(eog_epochs.plot_image(combine='mean', picks = m_or_g[0:-1])[0])
        list_of_desc.append('mean_EOG_epoch_'+m_or_g)

        #averaging the ECG epochs together:
        list_of_figs_ecg_sensors.append(eog_epochs.average().plot_joint(picks = m_or_g[0:-1]))
        list_of_desc_fig_ecg_sensors.append('EOG_field_pattern_sensors_'+m_or_g)

    list_of_figs += list_of_figs_ecg_sensors
    list_of_desc += list_of_desc_fig_ecg_sensors

    output_format = 'matplotlib'

    return list_of_figs, list_of_desc, output_format


