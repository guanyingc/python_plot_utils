import argparse
import os
import sys
import numpy as np
from plot_agent import PlotAgent

from IPython.core import ultratb
sys.excepthook = ultratb.FormattedTB(call_pdb=True)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('conf_file', default='', help='path of the config')
    parser.add_argument('--save_prefix', default='', help='append string to the save filename')
    parser.add_argument('--format', default='pdf', help='overwrite the save figure format, pdf|png|jpg')
    args = parser.parse_args()
    # args, unknown = parser.parse_known_args()
    return args


def main(args):
    plotAgent = PlotAgent()

    """ Load config """
    conf = plotAgent.parse_config(args.conf_file, strict=False)
        
    """ Set save filename """
    if args.format is not None:
        conf['format'] = args.format
    save_name = plotAgent.get_save_name(args.save_prefix)

    if conf['plot_type'] in ['ploty', 'plotxy', 'plottwins']:
        """ plot curves """
        plot_curves(args, save_name)

    elif conf['plot_type'] == 'plotbar':
        """ plot barchart """
        plot_barcharts(args, save_name)
    else:
        raise Exception('Unknown plot type %s' % conf['plot_type'])


def plot_curves(args, save_name):
    """ Plot curves """

    from plot_agent import PlotCurveAgent
    plotCurveAgent = PlotCurveAgent()

    """ Load config """
    conf = plotCurveAgent.parse_config(args.conf_file)

    """ Read data """
    data = plotCurveAgent.load_data_from_file(conf['datafile'], max_point_num=conf['max_point_num'])
    print('data', data)

    if conf['plot_type'] == 'ploty':
        """ The input data only contains Y values, the X values are generated as [0, ..., len(Y)]"""
        data_y = data
        data_x = [np.array(range(len(y)), dtype=float) for y in data_y]  # set x as [0, len(y)]

    elif conf['plot_type'] == 'plotxy':
        """ The input data contains both X and Y values """
        data_x = data[::2]
        data_y = data[1::2]

    elif conf['plot_type'] == 'plottwins':
        """ The input data only contains Y values. Plot figure with two different Y-axis """
        data0_xy = [np.array(range(len(data[0])), dtype=float), data[0]]
        data1_xy = [np.array(range(len(data[1])), dtype=float), data[1]]

    else:
        raise Exception('Unknown plot type %s' % conf['plot_type'])


    """ Configure figure layout"""
    fig, ax = plotCurveAgent.config_layout(conf, tight=True)

    """ Start ploting """
    if conf['plot_type'] == 'plottwins':
        plotCurveAgent.plot_twins_yaxis(ax, data0_xy, data1_xy, conf)

    else:
        """ Whether to sort data values """
        if conf['sort_data'] != 'None':
            data_x, data_y = plotCurveAgent.sort_data(data_x, data_y, sort=conf['sort_data'])

        plotCurveAgent.plot_xy(ax, data_x, data_y, conf)

    plotCurveAgent.save_fig(save_name)


def plot_barcharts(args, save_name):
    """ Plot barcharts """

    from plot_agent import PlotBarAgent
    plotBarAgent = PlotBarAgent()

    """ Load config """
    conf = plotBarAgent.parse_config(args.conf_file)
    data = plotBarAgent.load_data_from_file(conf['datafile'])
    print('data', data)

    """ Configure figure layout"""
    fig, ax = plotBarAgent.config_layout(conf, tight=True)

    plotBarAgent.plot_barchart(ax, data, conf)
    plotBarAgent.save_fig(save_name)

if __name__ == '__main__':
    args = parse_arguments()
    main(args)
