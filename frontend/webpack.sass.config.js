const path = require('path');
const glob = require('glob');

const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const RemoveEmptyScriptsPlugin = require('webpack-remove-empty-scripts');

const isProduction = process.env.NODE_ENV === 'production';

const stylesHandler = MiniCssExtractPlugin.loader;

const config = {
    entry: {
        nav: path.resolve(__dirname, '../python/nav/web/sass/nav.scss'),
        ...glob.sync('../python/nav/web/sass/nav/**.scss').filter(v => !path.parse(v).name.startsWith('_')).reduce(function (obj, el) {
            obj[`nav/${path.parse(el).name}`] = el;
            return obj
        }, {}),
        'font-awesome/font-awesome': path.resolve(__dirname, '../python/nav/web/sass/font-awesome/font-awesome.scss'),
    },
    output: {
        path: path.join(__dirname, '../python/nav/web/static/css'),
        clean: true,
    },
    devServer: {
        open: true,
        host: 'localhost',
    },
    plugins: [
        new MiniCssExtractPlugin(),
        new RemoveEmptyScriptsPlugin(),
    ],
    module: {
        rules: [
            {
                test: /\.s[ac]ss$/i,
                use: [stylesHandler, 'css-loader', 'sass-loader'],
            },
            {
                test: /\.(eot|svg|ttf|woff|woff2|png|jpg|gif)$/i,
                type: 'asset'
            },
        ],
    },
};

module.exports = () => {
    if (isProduction) {
        config.mode = 'production';


    } else {
        config.mode = 'development';
    }
    return config;
};
