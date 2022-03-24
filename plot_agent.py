"""
A simple wrapper for pyplot
"""
import os
import numpy as np
import matplotlib; matplotlib.use('agg')
import matplotlib.pyplot as plt

""" Set font """
from matplotlib import rcParams
rcParams['font.family'] = "Times New Roman"
# rcParams['font.family'] = 'serif' #'sans-serif'


class PlotAgent(object):
    """ Base helper class for plotting, its subclasses include PlotCurveAgent and PlotBarAgent"""

    def __init__(self):

        """ Configuration parameterss
        There are four types of parameters, including FLOAT, STRING, LIST OF STRING, and BOOL.
        When parsing parameters from the config file, the data type is determined by the default value in self.config
        """
        self.conf = {
                # Plot type: ploty|plotxy|plottwins|plotbar
                'plot_type': 'ploty',

                # Figure format: pdf|jpg|png
                'format': 'pdf',

                # Canvas: width, height, and dpi
                'width': 3,
                'height': 3,
                'dpi': 220,

                # Title:
                'title': '',
                'title_font': 'x-large',

                # Color
                'color': self.get_colors(),

                # Label:
                'xlabel': '',
                'xlabel_font': 'x-large',
                'ylabel': [],  # possibly two ylabels (in twin mode), so we use a list to store ylable
                'ylabel_font': 'x-large',

                # Tick:
                # https://www.tutorialspoint.com/matplotlib/matplotlib_setting_ticks_and_tick_labels.htm
                'xticklabel': [],
                'xtick_font': 'x-large',
                'xtick_rot': 0,
                'xtick_path': '',  # path to the xtick values

                'yticklabel': [],
                'ytick': [],
                'ytick_font': 'x-large',
                'ytick_rot': 0,

                # Value range
                'x_min': float('inf'),
                'x_max': float('-inf'), # range of the x-axis
                'y_min': [],  # set ymin/ymax as list as it is helpful for twins Y-axis
                'y_max': [],

                # Legend: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html
                'legend_loc': 'upper left',
                'legend': [],  # name of the legends
                'legend_ncol': 1,  # column number in the legend
                'legend_font': 'x-large',
                'bbox_to_anchor': [],  # used in plot_twins_yaxis, manually adjust two legends
                'custom_legend': False,

                # Grid
                'grid_on': True,

                # Data
                'datafile': [],  # each file stores the data of a curve
                'max_point_num': 1000,  # limits the maximum number of points
                'sort_data': 'None',  # sort Y values based on the first curve, options: None|ascend|descend
                }

        """ Special symbols in the configuration file *.conf
            When parsing the config file, lines start with # will be ignored,
            lines start with ! will be parsed and set
        """
        self.ignore_symbols = ['#', '##']
        self.config_symbols = ['!']
        self.space_symbol = '&' # Values in conf file containing & will be replaced by space

    def get_config(self):
        return self.conf

    def read_list(self, list_path, ignore_head=False):
        lists = []
        with open(list_path) as f:
            lists = f.read().splitlines()
        if ignore_head:
            lists = lists[1:]
        return lists

    def parse_config(self, fname, strict=True):
        """ Load and parse the configuration file
        if strict is True, unknown params will trigger an error
        """
        lines = self.read_list(fname)
        conf = self.conf

        for idx, line in enumerate(lines):
            line_splits = line.strip().split(' ')
            
            """ Check flag """
            flag = line_splits[0]
            if (flag in self.ignore_symbols) or (flag == '') or (flag[0] in self.ignore_symbols):
                continue
            if flag not in self.config_symbols:
                raise Exception('Unknown flag in the config %s' % flag)
                break

            param, val = line_splits[1], line_splits[2]

            if param in conf:
                if type(conf[param]) in [float, int]:
                    conf[param] = float(val)
                elif type(conf[param]) == str:
                    conf[param] = val.replace(self.space_symbol, ' ')
                elif type(conf[param]) == list:
                    conf[param] = [v.replace(self.space_symbol, ' ') for v in line_splits[2:]]
                elif type(conf[param]) == bool:
                    conf[param] = True if int(val) == 1 else False
                else:
                    raise Exception('Unknown parameters type: %s' % param)
            else:
                if strict:
                    raise Exception('Unknown parameters: %s' % param)

        """ Check path of the data files"""
        for i, df in enumerate(conf['datafile']):
            if not os.path.exists(df):
                """ Use relative path """
                dirname = os.path.dirname(fname)
                conf['datafile'][i] = os.path.join(dirname, df)

        conf['confname'] = fname
        for k, v in conf.items():
            print(k, v)
        return conf

    def load_data_from_file(self, files, max_point_num=100, skip=0, nan_value=0, max_curve_num=-1):
        """ Load data from list of files, data of each curve is stored in a file"""
        if type(files) is not list:
            files = [files]

        max_point_num = int(max_point_num)
        data = []
        for f in files:
            print('Loading File: %s' % f)
            raw_data = np.genfromtxt(f, skip_header=skip)
            raw_data[np.isnan(raw_data)] = nan_value

            if raw_data.ndim == 1:
                data.append(raw_data[:max_point_num])
            elif raw_data.ndim == 2:
                # If contains multiple column data, split it into multiple separate columns
                raw_data = np.split(raw_data, raw_data.shape[1], axis=1)
                for i in range(len(raw_data)):
                    data.append(raw_data[i][:max_point_num, 0])
        if max_curve_num > 0:
            data = data[:int(max_curve_num)]
        return data

    def get_save_name(self, save_prefix):
        """ Config save figure name"""
        save_dir = os.path.dirname(self.conf['confname'])
        parent_dir = os.path.basename(save_dir)
        conf_name = os.path.splitext(os.path.basename(self.conf['confname']))[0]

        save_name = save_prefix + parent_dir + '_' + conf_name + '.' + self.conf['format']
        save_name = os.path.join(save_dir, save_name)
        print('Save name: %s' % save_name)
        return save_name

    def config_layout(self, conf, row=1, col=1, tight=True):
        """ Define the canvas layout
        https://matplotlib.org/devdocs/gallery/subplots_axes_and_figures/figure_size_units.html
        """
        fig, ax = plt.subplots(row, col, figsize=(col*conf['width'], row*conf['height']),
                dpi=conf['dpi'], facecolor='w', edgecolor='k')
        if tight:
            fig.tight_layout()
        return fig, ax

    def get_colors(self):
        """ https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html
            https://matplotlib.org/3.5.1/tutorials/colors/colors.html
        """
        return ['r', 'k', 'b', 'g', 'y', 'm', 'c',
                'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']
    
    def decorate_plot(self, ax, conf):
        """ Place title, xlabel, ylabel """
        if conf['title'] not in ['', 'None', None]:
            ax.set_title(conf['title'], fontsize=conf['title_font'], fontweight='book')

        if conf['xlabel'] not in ['', 'None', None]:
            ax.set_xlabel(conf['xlabel'], fontsize=conf['xlabel_font'], fontweight='book')

        if len(conf['ylabel']) > 0:  # if exists ylabel
            if conf['ylabel'][0] not in ['', 'None', None]:
                ax.set_ylabel(conf['ylabel'][0], fontsize=conf['ylabel_font'], fontweight='book')

    def save_fig(self, save_name):
        plt.savefig(os.path.join(save_name), bbox_inches='tight')

    def close_fig(self, fig):
        plt.close(fig)


class PlotCurveAgent(PlotAgent):
    """ Helper class for plotting curves """

    def __init__(self):
        super(PlotCurveAgent, self).__init__()

        """ Configuration parameterss
        Add parameters for curves
        """
        self.conf.update({
                # Line:
                # https://matplotlib.org/2.1.2/api/_as_gen/matplotlib.pyplot.plot.html
                'linewidth': 3,
                'line_style': ['-'],
                'max_curve_num': -1,
                'markersize': 6,
                'marker': self.get_default_markers(),

                # Dot:
                'draw_dot': 0,  # if plot dot?
                'dotsize': 8,  # dot setting
                })

    def get_default_markers(self):
        """ https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html """
        return ['d', 'v', '1', '8', 'o', '^', '<', '>', 's', '*', 'p']

    def plot_xy(self, ax, xs, ys, conf, decorate=True):
        """
        ax: handler from plt.subplots()
        xs: x values, list of array
        ys: y values, list of array
        decorate: if put title, labels, etc.
        """
        for idx, (x, y) in enumerate(zip(xs, ys)):

            if conf['draw_dot']:
                ax.scatter(x, y, color=conf['color'][idx], s=conf['dotsize']*conf['dotsize'])
            else:  # Draw lines
                line_style = conf['line_style'][idx] if len(conf['line_style']) > idx else '-'
                ax.plot(x, y, color=conf['color'][idx], linestyle=line_style, linewidth=conf['linewidth'],
                        marker=conf['marker'][idx], markersize=conf['markersize'])
        
        """ Set value range of the x- and y-axis """
        x_min, x_max = self.set_xmin_xmax(np.min(xs), np.max(xs), conf)
        y_min, y_max = self.set_ymin_ymax(np.min(ys), np.max(ys), conf)
        print([x_min, x_max, y_min, y_max])
        ax.axis([x_min, x_max, y_min, y_max])

        """ put title, labels, etc """
        if decorate:
            self.decorate_plot(ax, conf, xticks=xs[0], yticks=[])

    def decorate_plot(self, ax, conf, xticks=[], yticks=[]):
        """ Place title, xlabel, ylabel, xticklabel, yticklabel, grid, etc """

        """ Call baes class method to place title, xlabel, ylabel """
        super(PlotCurveAgent, self).decorate_plot(ax, conf)

        """ Overwrite xtick if specify xtick_path """
        xtick_path = conf['xtick_path']
        if xtick_path != '':
            """ Use relative path """
            if not os.path.exists(xtick_path):
                xtick_path = os.path.dirname(conf['confname']) + '/' + xtick_path
            conf['xticklabel'] = [m.strip() for m in open(xtick_path).readlines()]

        self.set_xticks(ax, conf, xticks, conf['xticklabel'])
        self.set_yticks(ax, conf, yticks, conf['yticklabel'])

        self.set_legends(ax, conf, conf['legend'])

        if conf['grid_on']:
            ax.grid()
        ax.set_axisbelow(True) # Set grid below objects

    def set_ymin_ymax(self, y_min, y_max, conf):
        if len(conf['y_max']) > 0:
            y_max = float(conf['y_max'][0])
        if len(conf['y_min']) > 0:
            y_min = float(conf['y_min'][0])
        return y_min, y_max

    def set_xmin_xmax(self, x_min, x_max, conf):
        if conf['x_max'] > float('-inf'):
            x_max = float(conf['x_max'])
        if conf['x_min'] < float('inf'):
            x_min = float(conf['x_min'])
        return x_min, x_max

    def set_xticks(self, ax, conf, xticks, xticklabels, order=[]):
        ax.tick_params(axis='x', labelsize=conf['xtick_font'])
        if len(xticklabels) == 0:
            return

        if len(xticks) == 0:
            xticks = range(len(xticklabels))

        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        plt.setp(ax.get_xticklabels(), rotation=conf['xtick_rot'])

    def set_yticks(self, ax, conf, yticks, yticklabels):
        ax.tick_params(axis='y', labelsize=conf['ytick_font'])
        if len(yticklabels) == 0:
            return

        if len(yticks) == 0:
            yticks = range(len(yticklabels))
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticklabels)
        plt.setp(ax.get_yticklabels(), rotation=conf['ytick_rot'])

    def set_legends(self, ax, conf, legends=[]):
        if len(legends) == 0:
            return

        if conf['custom_legend']:
            self.custom_legend(ax, conf)
        else:
            legend = ax.legend(legends, fontsize=conf['legend_font'], loc=conf['legend_loc'],
                ncol=int(conf['legend_ncol']))
            legend.get_frame().set_edgecolor('0.4')

    def plot_twins_yaxis(self, ax, data0_xy, data1_xy, conf):
        """ Plot two curves with two different Y-axis"""

        def split_config(conf):
            """ Split the conf into two conf
            specifically, if a parameter is of list type, split it into two parts,
            other parameters will make a copy
            """
            conf1, conf2 = {}, {}
            for k in conf:
                if type(conf[k]) == list and len(conf[k]) == 2:
                    conf1[k], conf2[k] = [conf[k][0]], [conf[k][1]]
                else:
                    conf1[k], conf2[k] = conf[k], conf[k]
            return conf1, conf2

        conf1, conf2 = split_config(conf)

        """ Create a twin ax"""
        ax2 = ax.twinx()

        """ Don't put labels in the plot_xy() """
        self.plot_xy(ax, [data0_xy[0]], [data0_xy[1]], conf1, decorate=False)
        self.plot_xy(ax2, [data1_xy[0]], [data1_xy[1]], conf2, decorate=False)

        if conf['title'] not in ['', 'None', None]:
            ax.set_title(conf['title'], fontsize=conf['title_font'], fontweight='book')

        if conf['xlabel'] != '':
            ax.set_xlabel(conf['xlabel'], fontsize=conf['xlabel_font'], fontweight='book')

        if len(conf1['ylabel']) > 0:
            ax.set_ylabel(conf1['ylabel'][0], color=conf1['color'][0], fontsize=conf['ylabel_font'], fontweight='book')

        if len(conf2['ylabel']) > 0:
            ax2.set_ylabel(conf2['ylabel'][0], color=conf2['color'][0], fontsize=conf['ylabel_font'], fontweight='book')

        self.set_xticks(ax, conf, range(len(conf['xticklabel'])), conf['xticklabel'], order=[])

        ax.tick_params(axis='y', labelcolor=conf1['color'][0], labelsize=conf['ytick_font'])
        ax2.tick_params(axis='y', labelcolor=conf2['color'][0], labelsize=conf['ytick_font'])

        """ bbox_to_anchor
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html
        A 2-tuple (x, y) places the corner of the legend specified by loc at x, y.
        The bottom left of the figure is (0, 0) and the top right is (1, 1).
        For example, to put the legend's upper right-hand corner in the center of
        the axes (or figure) the following keywords can be used:
        loc='upper right', bbox_to_anchor=(0.5, 0.5)
        """
        box_x1, box_y1, box_x2, box_y2 = map(float, conf['bbox_to_anchor'][:4])
        ax.legend(conf1['legend'], fontsize=conf['legend_font'], loc=conf['legend_loc'], bbox_to_anchor=(box_x1, box_y1))
        ax2.legend(conf2['legend'], fontsize=conf['legend_font'], loc=conf['legend_loc'], bbox_to_anchor=(box_x2, box_y2))

        if conf['grid_on']:
            ax.grid()

    def custom_legend(self, ax, conf):
        """ Customize the legend
        This code is hardcode for this specific example, just for demo
        """
        from matplotlib.legend_handler import HandlerBase
        class AnyObjectHandler(HandlerBase):
            def create_artists(self, legend, orig_handle,
                               x0, y0, width, height, fontsize, trans):
                l1 = plt.Line2D([x0,y0+width], [0.7*height,0.7*height],
                               linestyle=orig_handle[1], color=orig_handle[0])
                l2 = plt.Line2D([x0,y0+width], [0.3*height,0.3*height],
                               linestyle=orig_handle[3], color=orig_handle[2])
                return [l1, l2]
        handle = []
        for i in range(len(conf['legend'])):
            handle.append((conf['color'][2*i], conf['line_style'][2*i],
                          conf['color'][2*i+1], conf['line_style'][2*i+1]))
        print(handle)
        plt.legend(handle, conf['legend'], handler_map={tuple: AnyObjectHandler()},
                fontsize=conf['legend_font'], loc=conf['legend_loc'], ncol=int(conf['legend_ncol']))

    def get_data_order(self, xs, ys, sort='None'):
        values = ys[0]  # sorted by the first curve
        if sort == 'None':
              # original order, from 0 to len(values)
            order = list(range(len(values)))
        else:
            order = np.argsort(values)  # ascend
            if sort == 'descend':  # descend
                order = order[::-1]
        return order
    
    def sort_data(self, xs, ys, sort='None'):
        """ Check if the input are valid"""
        assert sort in ['None', 'ascend', 'descend']

        for i in range(1, len(xs)):
            if not np.array_equal(xs[i-1], xs[i]):
                raise Exception('x values are not equal, cannot be sorted')

        if sort == 'None': # Do not sort
            return xs, ys
        
        order = np.argsort(ys[0])  # ascend, sorted by y values of the first curve
        if sort == 'descend':
            order = order[::-1]

        for i in range(len(xs)):
            ys[i] = ys[i][order]

        if len(self.conf['xticklabel']) > 0:  # sort xticklabel as well
            self.conf['xticklabel'] = [self.conf['xticklabel'][id] for id in order]
        return xs, ys


class PlotBarAgent(PlotCurveAgent):
    """ Helper class for plotting curves """

    def __init__(self):
        super(PlotBarAgent, self).__init__()

        """ Configuration parameterss
        Add parameters for barcharts
        """
        self.conf.update({
                # Bar:
                'bar_width': 0.2,
                'color': self.get_colors(),
                'opacity': [0.9],  # transparency of the bar, 1 indicates solid color

                # Text
                'put_text': True,
                'text_font': 13,
                'text_prec': '',  # precision of values in the barchart, e.g., %.2f, %.1f
                'percentage': False,  # Show values in percentage
                })

    def load_data_from_file(self, files, skip=0):
        """
        Assume only one file. The file contains a 2D array.
        Each column corresponds to a group.
        The number of row equals to the number of bars in a group 
        e.g., Group1, Group2, Group3, ...
        """
        assert len(files) == 1
        raw_data = np.genfromtxt(files[0], skip_header=skip)
        if raw_data.ndim == 1:
            raw_data = raw_data.reshape(1, -1)
        return raw_data

    def plot_barchart(self, ax, data, conf):
        """
        ax: handler from plt.subplots()
        data: 2D array, column number is the group number, row number is the bar number in each group
        """
        ngroups = data.shape[1]
        nbars = data.shape[0]

        conf['ngroups'] = ngroups  # Cached ngroups and nbars for later usage
        conf['nbars'] = nbars

        x_start = np.arange(1, ngroups + 1)  # x values of the first bar of all groups
        conf['x_start'] = x_start

        for i in range(nbars):
            """ Plot each bar in all gruops """
            y_vals = data[i][:]

            x_vals = x_start + i * conf['bar_width']  # x values of the current bars

            alpha = conf['opacity'][i] if len(conf['opacity']) > i else conf['opacity'][0]

            # The bars with be plotted centered on the x values
            rects = ax.bar(x_vals, y_vals, conf['bar_width'], alpha=float(alpha), color=conf['color'][i])

            if conf['put_text']:
                # might need to tune this param if text overlapped with bar
                vertical_dist = data.max() / 100
                self.put_text(ax, x_vals, y_vals, vertical_dist, conf=conf)

        """ Set value range of the y-axis """
        y_min, y_max = self.set_ymin_ymax(np.min(data), np.max(data), conf)
        ax.set_ylim([y_min, y_max])

        """ put title, labels, etc """
        self.decorate_bar(ax, conf)

    def decorate_bar(self, ax, conf):
        """ Place title, xlabel, ylabel, xticklabel, yticklabel, grid, etc """

        """ Call baes class method to place title, xlabel, ylabel """
        super(PlotCurveAgent, self).decorate_plot(ax, conf)

        if len(conf['xticklabel']) > 0:
            """ We have to set the xtick values to the center of each group 
            x_start is the center of the first bar, we just need to add 1/2*(nbar-1)*bar_width to the xstart
            """
            xticks = conf['x_start'] + 0.5 * (conf['nbars'] - 1) * conf['bar_width']
            assert (len(xticks) == len(conf['xticklabel'])), "The number of xticklabels should be \
                    the same as the xticks, %d !=%d" % (len(conf['xticklabel']), len(xticks))
            ax.set_xticks(xticks)
            ax.set_xticklabels(conf['xticklabel'], fontsize=conf['xtick_font'])

        if len(conf['yticklabel']) > 0:
            ax.set_yticks(list(map(float, conf['ytick'])))
            ax.set_yticklabels(conf['yticklabel'], fontsize=conf['ytick_font'])

        ax.tick_params(axis='y', labelsize=conf['ytick_font'])

        if len(conf['legend']) > 0:
            """ bbox_to_anchor
            https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html
            A 2-tuple (x, y) places the corner of the legend specified by loc at x, y.
            The bottom left of the figure is (0, 0) and the top right is (1, 1).
            For example, to put the legend's upper right-hand corner in the center of
            the axes (or figure) the following keywords can be used:
            loc='upper right', bbox_to_anchor=(0.5, 0.5)
            """
            box_x, box_y = map(float, conf['bbox_to_anchor'][:2])
            ax.legend(conf['legend'], bbox_to_anchor=(box_x, box_y), loc=conf['legend_loc'], 
                    fontsize=conf['legend_font'], ncol=int(conf['legend_ncol']), handletextpad=0.1)

        if conf['grid_on']:
            ax.yaxis.grid()  # only show grid lines for yaxis

    def put_text(self, ax, x_vals, y_vals, vertical_dist=0.5, conf={}):
        """ Put text on the barchart"""

        for x, y in zip(x_vals, y_vals):

            """ Set text precision """
            if conf['text_prec'] == '':
                prec = '%.2f' if y < 1 else '%.1f'
            else:
                prec = conf['text_prec']

            if conf['percentage']:
                text = '%d%%' % (y * 100)
            else:
                text = prec % y
            ax.text(x, y + vertical_dist, text, fontsize=conf['text_font'], 
                    horizontalalignment='center')

