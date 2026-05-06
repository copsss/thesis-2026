# -*- coding: utf-8 -*-
"""
自动为论文中的英文术语添加 \textit{} 标记
处理规则：
1. 只处理2个字符以上的纯英文单词
2. 跳过 LaTeX 命令（如 \chapter, \section 等）
3. 跳过已经在 \textit{}, \upcite{}, \ref{}, \label{} 等命令中的英文
4. 跳过数学模式 $...$ 中的英文
5. 跳过已存在的英文命令参数
"""

import re
import sys

# LaTeX 命令列表（不需要处理的命令）
LATEX_COMMANDS = [
    'chapter', 'section', 'subsection', 'subsubsection',
    'begin', 'end', 'cite', 'upcite', 'ref', 'label',
    'include', 'input', 'usepackage', 'documentclass',
    'newcommand', 'def', 'textbf', 'textit', 'emph',
    'item', 'hline', 'multicolumn', 'multirow',
    'centering', 'caption', 'includegraphics',
    'bibitem', 'bibliography', 'addcontentsline',
    'tableofcontents', 'listoffigures', 'listoftables',
    'setlength', 'renewcommand', 'newtheorem', 'newfont',
    'providecommand', 'definecolor', 'usetikzlibrary',
    'pgfplotsset', 'algnewcommand', 'floatname',
    'State', 'Statex', 'If', 'Else', 'EndIf', 'For', 'EndFor',
    'While', 'EndWhile', 'Return', 'Require', 'Ensure',
    'left', 'right', 'frac', 'sum', 'int', 'prod', 'sqrt',
    'cdot', 'times', 'div', 'pm', 'mp', 'leq', 'geq', 'neq',
    'approx', 'equiv', 'propto', 'infty', 'partial', 'nabla',
    'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta',
    'eta', 'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu',
    'xi', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi',
    'chi', 'psi', 'omega', 'Gamma', 'Delta', 'Theta',
    'Lambda', 'Xi', 'Pi', 'Sigma', 'Upsilon', 'Phi', 'Psi', 'Omega',
    'rmfamily', 'bfseries', 'itshape', 'scshape', 'ttfamily',
    'small', 'footnotesize', 'scriptsize', 'tiny', 'large', 'Large',
    'huge', 'Huge', 'zihao', 'zihaosan', 'zihaosi', 'zihaoxiaosi',
    'zihaoxiaosan', 'zihaowu', 'zihaoer', 'zihaonankaidaxue',
    'selectfont', 'baselineskip', 'vskip', 'hskip', 'vspace',
    'hspace', 'quad', 'qquad', 'par', 'indent', 'noindent',
    'clearpage', 'cleardoublepage', 'newpage', 'pagebreak',
    'maketitle', 'tablepage', 'NKTsetup', 'NKTtitlepage',
    'NKTdeclaration', 'abstract', 'zhaiyao', 'guanjianci',
    'keywords', 'endkeywords', 'endabstract', 'endzhaiyao',
    'endguanjianci', 'spacing', 'endspacing', 'algorithm',
    'endalgorithm', 'algorithmic', 'endalgorithmic',
    'tikzpicture', 'endtikzpicture', 'figure', 'endfigure',
    'table', 'endtable', 'tabular', 'endtabular', 'equation',
    'endequation', 'align', 'endalign', 'gather', 'endgather',
    'enumerate', 'endenumerate', 'itemize', 'enditemize',
    'description', 'enddescription', 'cases', 'endcases',
    'split', 'endsplit', 'aligned', 'endaligned', 'array',
    'endarray', 'matrix', 'endmatrix', 'pmatrix', 'endpmatrix',
    'bmatrix', 'endbmatrix', 'vmatrix', 'endvmatrix',
    'Bmatrix', 'endBmatrix', 'minipage', 'endminipage',
    'resizebox', 'makeatletter', 'makeatother', 'makebox',
    'framebox', 'parbox', 'raisebox', 'rule', 'hrule', 'vrule',
    'cline', 'vline', 'multicolumn', 'multirow', 'rowcolor',
    'cellcolor', 'columncolor', 'arrayrulecolor', 'doublerulesepcolor',
    'caption', 'subcaption', 'subfigure', 'subfloat',
    'listoffigures', 'listoftables', 'printbibliography',
    'bibliographystyle', 'citeauthor', 'citeyear', 'citep', 'citet',
    'footnote', 'footnotemark', 'footnotetext',
    'marginpar', 'reversemarginpar', 'normalmarginpar',
    'thispagestyle', 'pagestyle', 'markboth', 'markright',
    'pagenumbering', 'setcounter', 'addtocounter', 'stepcounter',
    'refstepcounter', 'arabic', 'roman', 'Roman', 'alph', 'Alph',
    'fnsymbol', 'numberwithin', 'eqref', 'pageref', 'nameref',
    'hyperref', 'url', 'href', 'nolinkurl', 'texorpdfstring',
    'pdfstringdefDisableCommands', 'phantomsection',
    'currentpdfbookmark', 'subpdfbookmark', 'belowpdfbookmark',
    'texorpdfstring', 'CJKnumber', 'CJKdigits', 'CJKtilde',
    'CJKspace', 'CJKecglue', 'CJKglue', 'CJKsetecglue',
    'CJKkern', 'CJKsymbols', 'CJKpunctsymbol', 'xeCJKsetup',
    'setCJKmainfont', 'setCJKsansfont', 'setCJKmonofont',
    'setCJKfamilyfont', 'newCJKfontfamily', 'CJKfamily',
    'setmainfont', 'setsansfont', 'setmonofont', 'setmathfont',
    'setmathrm', 'setmathsf', 'setmathtt', 'setmathsfont',
    'setboldmathrm', 'setmathfontface', 'DeclareMathAlphabet',
    'SetMathAlphabet', 'DeclareSymbolFont', 'SetSymbolFont',
    'DeclareMathSymbol', 'DeclareMathDelimiter', 'DeclareMathAccent',
    'DeclareMathRadical', 'DeclareMathSizes', 'setstretch',
    'begin', 'end', 'newenvironment', 'renewenvironment',
    'newcounter', 'renewcounter', 'newlength', 'newsavebox',
    'newif', 'newtoks', 'newinsert', 'newread', 'newwrite',
    'openin', 'closein', 'read', 'openout', 'closeout', 'write',
    'immediate', 'protect', 'unskip', 'ignorespaces', 'null',
    'obeycr', 'restorecr', 'active', 'unskip', 'unkern', 'unpenalty',
    'discretionary', 'allowbreak', 'nolinebreak', 'linebreak',
    'nobreak', 'eject', 'supereject', 'goodbreak', 'smallbreak',
    'medbreak', 'bigbreak', 'filbreak', 'vfil', 'vfill', 'vfilneg',
    'hfil', 'hfill', 'hfilneg', 'hss', 'vss', 'dotfill', 'hrulefill',
    'leftarrowfill', 'rightarrowfill', 'upbracefill', 'downbracefill',
    'strut', 'mathstrut', 'phantom', 'vphantom', 'hphantom',
    'smash', 'llap', 'rlap', 'clap', 'mathpalette', 'mathchoice',
    'buildrel', 'stackrel', 'underset', 'overset', 'sideset',
    'operatorname', 'DeclareMathOperator', 'DeclareMathOperator*',
    'limits', 'nolimits', 'displaylimits', 'text', 'intertext',
    'shortintertext', 'mbox', 'makebox', 'textnormal', 'textrm',
    'textsf', 'texttt', 'textup', 'textit', 'textsl', 'textsc',
    'textbf', 'textmd', 'em', 'emph', 'underline', 'overline',
    'bar', 'vec', 'tilde', 'hat', 'check', 'breve', 'acute',
    'grave', 'dot', 'ddot', 'dddot', 'ddddot', 'mathring', 'widetilde',
    'widehat', 'overrightarrow', 'overleftarrow', 'overleftrightarrow',
    'underrightarrow', 'underleftarrow', 'underleftrightarrow',
    'xrightarrow', 'xleftarrow', 'xleftrightarrow', 'xhookrightarrow',
    'xhookleftarrow', 'xmapsto', 'xtwoheadrightarrow', 'xtwoheadleftarrow',
    'overbrace', 'underbrace', 'overbracket', 'underbracket',
    'sqrt', 'root', 'frac', 'tfrac', 'dfrac', 'cfrac', 'binom',
    'tbinom', 'dbinom', 'genfrac', 'substack', 'subarray',
    'sideset', 'underset', 'overset', 'stackrel', 'buildrel',
    'pmb', 'boldsymbol', 'bm', 'text', 'intertext', 'shortintertext',
    'eqref', 'tag', 'notag', 'nonumber', 'displaybreak', 'allowdisplaybreaks',
    'shoveleft', 'shoveright', 'intertext', 'shortintertext',
    'mathrm', 'mathsf', 'mathtt', 'mathit', 'mathbf', 'mathnormal',
    'mathcal', 'mathscr', 'mathfrak', 'mathbb', 'mathbfcal',
    'mathbffrak', 'mathbfscr', 'mathds', 'textup', 'textlf',
    'textsw', 'textsc', 'textulc', 'textsi', 'textit', 'textbf',
    'textmd', 'textlf', 'textsb', 'texteb', 'textub', 'textlg',
    'textsm', 'textmicro', 'textfractionsolidus', 'textminus',
    'textasteriskcentered', 'textbullet', 'textperiodcentered',
    'textbardbl', 'textbackslash', 'textbraceleft', 'textbraceright',
    'textasciitilde', 'textasciicircum', 'textunderscore',
    'textquoteleft', 'textquoteright', 'textquotedblleft',
    'textquotedblright', 'textquotesingle', 'textquotedbl',
    'textdollar', 'textsterling', 'textyen', 'texteuro', 'textcent',
    'textflorin', 'textcurrency', 'textdegree', 'textordmasculine',
    'textordfeminine', 'textsection', 'textparagraph', 'textpilcrow',
    'textdagger', 'textdaggerdbl', 'textdoublebarwedge', 'textpm',
    'textmp', 'texttimes', 'textdiv', 'textfrac', 'textonehalf',
    'textonethird', 'texttwothirds', 'textonequarter', 'textthreequarters',
    'textonesuperior', 'texttwosuperior', 'textthreesuperior',
    'textsurd', 'textlnot', 'textneg', 'textapprox', 'textsim',
    'textsimeq', 'textcong', 'textequiv', 'textpropto', 'textinfty',
    'textprime', 'textdoubleprime', 'texttripleprime', 'textbackprime',
    'textRe', 'textIm', 'textell', 'textwp', 'textpartial', 'textnabla',
    'texthbar', 'texthslash', 'texteth', 'textthorn', 'textschwa',
    'textezh', 'textyogh', 'textglottalstop', 'textpipe', 'textturna',
    'textturnv', 'textturnw', 'textturny', 'textturnh', 'textturnm',
    'textturnr', 'textturnrrtail', 'textturnlonglegr', 'textpalhook',
    'textasciicaron', 'textasciibreve', 'textasciimacron', 'textasciidieresis',
    'textgravedbl', 'textacutedbl', 'texttildelow', 'textcircled',
    'textcircledP', 'textopenbullet', 'textbigcircle', 'textbullet',
    'textdiamond', 'textopenbullet', 'textbullet', 'textperiodcentered',
    'texttwelveudash', 'textthreequartersemdash', 'textquotestraightbase',
    'textquotestraightdblbase', 'texttwelveudash', 'textthreequartersemdash',
    'textemdash', 'textendash', 'textexclamdown', 'textquestiondown',
    'textvisiblespace', 'textcompwordmark', 'textcapitalcompwordmark',
    'textascendercompwordmark', 'textquoteright', 'textquoteleft',
    'textquotedblright', 'textquotedblleft', 'textdollar', 'textsterling',
    'textyen', 'texteuro', 'textcent', 'textflorin', 'textcurrency',
    'textdegree', 'textordmasculine', 'textordfeminine', 'textsection',
    'textparagraph', 'textpilcrow', 'textdagger', 'textdaggerdbl',
    'textdoublebarwedge', 'textbar', 'textbrokenbar', 'textpm', 'textmp',
    'texttimes', 'textdiv', 'textfrac', 'textonehalf', 'textonethird',
    'texttwothirds', 'textonequarter', 'textthreequarters', 'textonesuperior',
    'texttwosuperior', 'textthreesuperior', 'textsurd', 'textlnot',
    'textneg', 'textapprox', 'textsim', 'textsimeq', 'textcong', 'textequiv',
    'textpropto', 'textinfty', 'textprime', 'textdoubleprime', 'texttripleprime',
    'textbackprime', 'textdagger', 'textdaggerdbl', 'textbullet',
    'textopenbullet', 'textbigcircle', 'textperiodcentered', 'texttwelveudash',
    'textthreequartersemdash', 'textemdash', 'textendash', 'textexclamdown',
    'textquestiondown', 'textvisiblespace', 'textcompwordmark',
    'textcapitalcompwordmark', 'textascendercompwordmark', 'textquoteright',
    'textquoteleft', 'textquotedblright', 'textquotedblleft',
    # 数学符号命令
    'exp', 'log', 'ln', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
    'arcsin', 'arccos', 'arctan', 'sinh', 'cosh', 'tanh', 'coth',
    'lim', 'limsup', 'liminf', 'max', 'min', 'sup', 'inf', 'arg',
    'ker', 'dim', 'hom', 'deg', 'det', 'gcd', 'Pr', 'proj', 'mod',
    'bmod', 'pmod', 'pod', 'text', 'textbf', 'textit', 'textrm',
    'textsf', 'texttt', 'textup', 'textsl', 'textsc', 'textmd',
    'mathnormal', 'mathrm', 'mathsf', 'mathtt', 'mathit', 'mathbf',
    'mathcal', 'mathscr', 'mathfrak', 'mathbb', 'hat', 'tilde',
    'bar', 'vec', 'dot', 'ddot', 'acute', 'grave', 'breve', 'check',
    'mathring', 'widehat', 'widetilde', 'overline', 'underline',
    'overbrace', 'underbrace', 'overrightarrow', 'overleftarrow',
    'overleftrightarrow', 'underrightarrow', 'underleftarrow',
    'underleftrightarrow', 'xrightarrow', 'xleftarrow', 'sqrt',
    'frac', 'tfrac', 'dfrac', 'binom', 'tbinom', 'dbinom', 'genfrac',
    'sum', 'prod', 'coprod', 'int', 'oint', 'bigcap', 'bigcup',
    'bigsqcup', 'bigvee', 'bigwedge', 'bigodot', 'bigotimes',
    'bigoplus', 'biguplus', 'limits', 'nolimits', 'displaylimits',
    'infty', 'partial', 'nabla', 'triangle', 'forall', 'exists',
    'nexists', 'emptyset', 'varnothing', 'aleph', 'hbar', 'hslash',
    'ell', 'wp', 'Re', 'Im', 'prime', 'backprime', 'surd', 'top',
    'bot', 'angle', 'measuredangle', 'sphericalangle', 'complement',
    'mho', 'eth', 'Finv', 'Game', 'Bbbk', 'bigstar', 'diagup',
    'diagdown', 'blacklozenge', 'lozenge', 'bigcirc', 'square',
    'blacksquare', 'triangledown', 'triangleup', 'triangleleft',
    'triangleright', 'blacktriangle', 'blacktriangledown',
    'blacktriangleleft', 'blacktriangleright', 'vartriangle',
    'vartriangledown', 'trianglelefteq', 'trianglerighteq',
    'unlhd', 'unrhd', 'blacklozenge', 'lozenge', 'bigstar',
    # 颜色和绘图命令
    'color', 'textcolor', 'pagecolor', 'definecolor', 'colorlet',
    'SetSymbolFont', 'SetMathAlphabet', 'DeclareMathAlphabet',
    'DeclareMathVersion', 'SetMathVersion', 'definecolor', 'colorlet',
    'tikz', 'draw', 'fill', 'path', 'node', 'coordinate', 'rectangle',
    'circle', 'ellipse', 'arc', 'line', 'curve', 'grid', 'shade',
    'pattern', 'clip', 'useasboundingbox', 'scope', 'endscope',
    'foreach', 'pgfmath', 'pgfkeys', 'pgfdeclarelayer', 'pgfsetlayers',
    'pgfdeclareshape', 'pgfdeclareplotmark', 'pgfplotsset', 'axis',
    'endaxis', 'addplot', 'legend', 'pgfplotstable', 'pgfplotstableread',
    # 参考文献和引用
    'bibliography', 'bibliographystyle', 'cite', 'upcite', 'citep',
    'citet', 'citeauthor', 'citeyear', 'citeyearpar', 'citetext',
    'citealt', 'citealp', 'Cite', 'Citep', 'Citet', 'nocite',
    'fullcite', 'footcite', 'parencite', 'textcite', 'autocite',
    'smartcite', 'supercite', 'volcite', 'pvolcite', 'fvolcite',
    'ftvolcite', 'svolcite', 'tvolcite', 'avolcite', 'notecite',
    'pnotecite', 'fnotecite', 'bibentry', 'nobibliography',
    'defbibentryset', 'assignrefcontextkey', 'assignrefcontextkeyalias',
    'DeclareRefcontext', 'newrefcontext', 'beginrefcontext',
    'endrefcontext', 'Assignrefcontextkey', 'assignrefcontextkey',
    'printbibliography', 'printbibheading', 'printbiblist',
    'printbiblistheading', 'biblistname', 'bibnamedelima',
    'bibnamedelimb', 'bibnamedelimc', 'bibnamedelimd', 'bibnamedelimi',
    'bibinitperiod', 'bibinitdelim', 'bibinithyphendelim', 'bibindex',
    'bibxdata', 'bibrangedash', 'bibrangesep', 'bibrangeslash',
    'multicitedelim', 'multicitesubsep', 'multiciterangedelim',
    'multicitesubrangedelim', 'prenotedelim', 'postnotedelim',
    'compcitedelim', 'compciterangedelim', 'textcitedelim',
    'textciterangedelim', 'textcitecount', 'textcitetotal', 'textcitepre',
    'nameyeardelim', 'nametitledelim', 'titleyeardelim', 'ytsep',
    'ysep', 'tsep', 'postsep', 'multilistdelim', 'multilistsep',
    'multicitedelim', 'multicitesubsep', 'supercitedelim',
    # 定理环境
    'newtheorem', 'newtheorem*', 'theoremstyle', 'theorembodyfont',
    'theoremheaderfont', 'theorempreskipamount', 'theorempostskipamount',
    'qedsymbol', 'qed', 'openbox', 'closedbox', 'proof', 'endproof',
    'theorem', 'lemma', 'corollary', 'proposition', 'definition',
    'example', 'remark', 'note', 'case', 'claim', 'conjecture',
    'fact', 'hypothesis', 'notation', 'problem', 'question',
    'solution', 'Criterion', 'Assertion', 'Algorithm', 'Axiom',
    'Condition', 'Property', 'Assumption', 'Conclusion',
    # 算法环境
    'algsetup', 'alglineno', 'algblock', 'algcblock', 'algloop',
    'algcloop', 'algfunction', 'algpcfunction', 'algstore',
    'algrestore', 'algtext', 'algbegin', 'algend', 'algnewcommand',
    'algdef', 'algcdef', 'algnewblock', 'algnewloop', 'algnewfunction',
    'algrenewcommand', 'algrenewblock', 'algrenewloop', 'algrenewfunction',
    'Require', 'Ensure', 'State', 'Statex', 'If', 'Else', 'ElsIf',
    'EndIf', 'For', 'ForAll', 'While', 'Repeat', 'Until', 'Loop',
    'EndLoop', 'Function', 'EndFunction', 'Procedure', 'EndProcedure',
    'Call', 'Return', 'Print', 'Comment', 'Input', 'Output',
    # 文档结构和排版
    'frontmatter', 'mainmatter', 'backmatter', 'appendix',
    'listoffigures', 'listoftables', 'printindex', 'makeindex',
    'index', 'see', 'seealso', 'seename', 'alsoname', 'indexname',
    'indexspace', 'subitem', 'subsubitem', 'indexentry', 'theindex',
    'endtheindex', 'bibname', 'refname', 'contentsname', 'listfigurename',
    'listtablename', 'indexname', 'figurename', 'tablename', 'partname',
    'chaptername', 'sectionname', 'subsectionname', 'appendixname',
    'abstractname', 'proofname', 'algorithmname', 'lstlistingname',
    'exercisename', 'solutionname', 'theoremname', 'lemmaame',
    'corollaryname', 'propositionname', 'definitionname', 'examplename',
    'remarkname', 'notename', 'casename', 'claimname', 'conjecturename',
    'factname', 'hypothesisname', 'notationname', 'problemname',
    'questionname', 'algorithmcfname', 'algorithmicrequirename',
    'algorithmicensurename', 'algorithmiccommentname', 'algorithmicend',
    'algorithmicif', 'algorithmicelse', 'algorithmicelsif', 'algorithmicfor',
    'algorithmicforall', 'algorithmicwhile', 'algorithmicrepeat',
    'algorithmicuntil', 'algorithmicloop', 'algorithmicfunction',
    'algorithmicprocedure', 'algorithmicreturn', 'algorithmicstate',
    'algorithmicprint', 'algorithmiccomment', 'algorithmicand',
    'algorithmicor', 'algorithmicxor', 'algorithmicnot', 'algorithmicto',
    'algorithmicdownto', 'algorithmictrue', 'algorithmicfalse',
    'algorithmicinput', 'algorithmicoutput', 'algorithmicrequire',
    'algorithmicensure', 'algorithmicreturn', 'algorithmicupon',
    'algorithmicdoing', 'algorithmicwhen', 'algorithmicifmore',
    'algorithmicotherwise', 'algorithmicuntil', 'algorithmicwhile',
    # hyperref
    'hypersetup', 'href', 'url', 'nolinkurl', 'hyperbaseurl', 'hyperdef',
    'hyperref', 'hyperlink', 'hypertarget', 'hyperimage', 'hyperpage',
    'autoref', 'Autoref', 'ref*', 'pageref*', 'nameref*', 'pdfstringdef',
    'pdfbookmark', 'currentpdfbookmark', 'subpdfbookmark', 'belowpdfbookmark',
    'texorpdfstring', 'hypercalcbp', 'Acrobatmenu', 'TextField', 'CheckBox',
    'ChoiceMenu', 'PushButton', 'LayoutTextField', 'LayoutChoiceField',
    'LayoutCheckField', 'MakeRadioField', 'MakeCheckField', 'MakeTextField',
    'MakeChoiceField', 'ListBox', 'ComboBox', 'Reset', 'Submit', 'Form',
    'endForm', 'Field', 'endField', 'ChoiceMenu', 'TextField', 'CheckBox',
    # 表格相关
    'toprule', 'midrule', 'bottomrule', 'cmidrule', 'addlinespace',
    'morecmidrules', 'specialrule', 'specialrule', 'hhline', 'cline',
    'vline', 'hline', 'tabularnewline', 'newcolumntype', 'showcols',
    'multirow', 'multicolumn', 'rowcolor', 'cellcolor', 'columncolor',
    'arraybackslash', 'doublerulesepcolor', 'arrayrulecolor', 'extrarowheight',
    'aboverulesep', 'belowrulesep', 'defaultaddspace', 'heavyrulewidth',
    'lightrulewidth', 'belowbottomsep', 'abovetopsep', 'belowrulesep',
    'aboverulesep', 'cmidrulesep', 'cmidrulekern', 'morecmidrules',
    # 其他常用命令
    'today', 'TeX', 'LaTeX', 'LaTeXe', 'XeTeX', 'XeLaTeX', 'LuaTeX',
    'LuaLaTeX', 'pdfTeX', 'pdfLaTeX', 'BibTeX', 'MakeIndex', 'MiKTeX',
    'TeXLive', 'TeXShop', 'WinEdt', 'TeXworks', 'Overleaf', 'ShareLaTeX',
    'CTeX', 'xeCJK', 'CTEX', 'upcite', 'mathbf', 'boldsymbol', 'mathbb',
    'mathcal', 'mathscr', 'mathfrak', 'mathbbm', 'varmathbb', 'Bbb',
    'textsubscript', 'textsuperscript', 'textordmasculine', 'textordfeminine',
    'textasteriskcentered', 'textparagraph', 'textsection', 'textdagger',
    'textdaggerdbl', 'textbardbl', 'textbackslash', 'textbraceleft',
    'textbraceright', 'textasciitilde', 'textasciicircum', 'textunderscore',
    'textquoteleft', 'textquoteright', 'textquotedblleft', 'textquotedblright',
    'textquotesingle', 'textquotedbl', 'textdollar', 'textsterling',
    'textyen', 'texteuro', 'textcent', 'textflorin', 'textcurrency',
    'textdegree', 'textsection', 'textparagraph', 'textpilcrow',
    'textminus', 'textpm', 'textmp', 'textdiv', 'texttimes', 'textcdot',
    'textbullet', 'textopenbullet', 'textbigbullet', 'textperiodcentered',
    'textellipsis', 'textendash', 'textemdash', 'textexclamdown',
    'textquestiondown', 'textvisiblespace', 'textcompwordmark',
    'textcapitalcompwordmark', 'textascendercompwordmark', 'textquoteright',
    'textquoteleft', 'textquotedblright', 'textquotedblleft', 'textperthousand',
    'textpertenthousand', 'textfractionsolidus', 'textlnot', 'textsurd',
    'textmu', 'textDelta', 'textOmega', 'textpi', 'textSigma', 'textPhi',
    'textGamma', 'textTheta', 'textLambda', 'textXi', 'textPi', 'textSigma',
    'textUpsilon', 'textPhi', 'textPsi', 'textOmega', 'textalpha', 'textbeta',
    'textgamma', 'textdelta', 'textepsilon', 'textzeta', 'texteta', 'texttheta',
    'textiota', 'textkappa', 'textlambda', 'textmu', 'textnu', 'textxi',
    'textomikron', 'textpi', 'textrho', 'textsigma', 'texttau', 'textupsilon',
    'textphi', 'textchi', 'textpsi', 'textomega', 'textvarsigma', 'textvartheta',
    'textphi', 'textvarpi', 'textvarrho', 'textvarepsilon', 'textvarkappa',
    'textdigamma', 'textbackepsilon', 'texteth', 'textthorn', 'textschwa',
    'textezh', 'textyogh', 'textglottalstop', 'textpipe', 'textturna',
]

def should_skip_word(word, context_before, context_after):
    """
    判断是否应该跳过这个单词
    """
    # 跳过纯数字
    if word.isdigit():
        return True

    # 跳过单个字母（除了常见的数学符号）
    if len(word) == 1:
        return True

    # 跳过 LaTeX 命令
    if word in LATEX_COMMANDS:
        return True

    # 跳过文件扩展名
    if word.lower() in ['tex', 'pdf', 'png', 'jpg', 'jpeg', 'bib', 'sty', 'cls', 'def', 'cfg', 'fd', 'map', 'tfm', 'vf', 'pfb', 'ttf', 'otf']:
        return True

    # 跳过常见单位
    if word.lower() in ['mm', 'cm', 'm', 'km', 'nm', 'um', 'pm', 'fm', 'am',
                        'ms', 's', 'min', 'h', 'hr', 'day', 'week', 'month', 'year',
                        'hz', 'khz', 'mhz', 'ghz', 'thz',
                        'b', 'kb', 'mb', 'gb', 'tb', 'pb',
                        'v', 'mv', 'kv', 'ma', 'a', 'w', 'mw', 'kw',
                        'db', 'rad', 'deg', 'sr', 'lm', 'lx', 'cd',
                        'pa', 'kpa', 'mpa', 'gpa', 'atm', 'bar', 'mbar',
                        'j', 'kj', 'mj', 'ev', 'kev', 'mev', 'gev',
                        'k', 'mk', 'mol', 'l', 'ml', 'g', 'kg', 'mg', 'ug', 'ng',
                        'mps', 'kmps', 'mph', 'rpm', 'fps']:
        return True

    # 跳过数学模式中的变量名（周围有 $ 符号）
    if '$' in context_before or '$' in context_after:
        # 检查是否在数学模式内
        dollar_count_before = context_before.count('$')
        if dollar_count_before % 2 == 1:  # 奇数个$，说明在数学模式内
            return True

    return False


def process_line(line):
    """
    处理单行文本，为英文添加 \textit{}
    """
    # 匹配模式：2个或以上连续英文字母
    # 但避免匹配已经在命令中的内容

    result = []
    i = 0
    n = len(line)

    while i < n:
        # 检查是否是 LaTeX 命令（以 \ 开头）
        if line[i] == '\\':
            # 找到命令名
            j = i + 1
            while j < n and line[j].isalpha():
                j += 1
            if j > i + 1:
                cmd = line[i+1:j]
                if cmd in LATEX_COMMANDS:
                    # 这是已知命令，保留原样
                    result.append(line[i:j])
                    i = j
                    continue

        # 检查是否是英文单词
        if line[i].isalpha():
            # 收集连续的英文字母
            j = i
            while j < n and line[j].isalpha():
                j += 1
            word = line[i:j]

            # 获取上下文
            context_before = line[max(0, i-10):i]
            context_after = line[j:min(n, j+10)]

            # 检查是否应该跳过
            if should_skip_word(word, context_before, context_after):
                result.append(word)
            else:
                # 检查是否已经在 \textit{} 中
                if context_before.rstrip().endswith('\\textit{'):
                    result.append(word)
                # 检查是否在 \upcite{} 中
                elif '\\upcite{' in context_before and '}' not in context_before.split('\\upcite{')[-1]:
                    result.append(word)
                # 检查是否在 \ref{} 或 \label{} 中
                elif any(cmd in context_before for cmd in ['\\ref{', '\\label{', '\\eqref{', '\\pageref{', '\\nameref{']):
                    result.append(word)
                # 检查是否在 $...$ 数学模式中
                elif '$' in context_before and context_before.count('$') % 2 == 1:
                    result.append(word)
                else:
                    # 添加 \textit{}
                    result.append(f'\\textit{{{word}}}')

            i = j
        else:
            result.append(line[i])
            i += 1

    return ''.join(result)


def process_file(filepath):
    """
    处理单个文件
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # 跳过空行和纯注释行
        stripped = line.strip()
        if not stripped or stripped.startswith('%'):
            new_lines.append(line)
            continue

        # 处理行内内容，但保留行首的缩进
        leading_space = len(line) - len(line.lstrip())
        indent = line[:leading_space]
        content = line[leading_space:]

        # 处理内容
        new_content = process_line(content)

        new_lines.append(indent + new_content)

    new_content = '\n'.join(new_lines)

    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Processed: {filepath}")


def main():
    files = [
        'chapter1.tex',
        'chapter2.tex',
        'chapter3.tex',
        'chapter4.tex',
        'chapter5.tex',
        'abstract.tex',
    ]

    for filename in files:
        filepath = f'D:/underwater/thesis-2026/{filename}'
        try:
            process_file(filepath)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")


if __name__ == '__main__':
    main()
