(function() {
    const markdownContent = {{ result | tojson }};
    const htmlContent = marked.parse(markdownContent);
    document.getElementById("content-{{ loop.index }}").innerHTML = htmlContent;
})();