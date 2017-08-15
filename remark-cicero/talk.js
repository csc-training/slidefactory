remark.macros.scale = function (percentage) {
    var url = this;
    return '<img src="' + url + '" style="width: ' + percentage + '" />';
};
remark.macros.size = function (x,y) {
    var url = this;
    return '<img src="' + url + '" style="width: ' + x + 'px; height: ' + y + 'px" />';
};
remark.macros.author = function () {
    var url = this;
    return '<img src="' + url + '" class=author-pic />';
};
