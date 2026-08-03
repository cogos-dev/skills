#!/usr/bin/env zsh
# Preview powerline prompt themes with customizable colors
# Usage: theme_preview.sh              — show preset themes
#        theme_preview.sh palette      — 256-color picker
#        theme_preview.sh custom DIR_BG DIR_FG CLEAN_BG CLEAN_FG DIRTY_BG DIRTY_FG STATUS_BG STATUS_FG CHAR_COLOR [ERR_COLOR]

SEP=$'\ue0b0'
BRANCH=$'\ue0a0'
CROSS=$'\u2718'
CHEVRON=$'\u276f'
PLUSMINUS=$'\u00b1'
STAGED=$'\u271a'
NC=$'\e[0m'
BOLD=$'\e[1m'

fg256() { print -n "\e[38;5;${1}m"; }
bg256() { print -n "\e[48;5;${1}m"; }

render_prompt() {
    local label="$1" status_bg="$2" status_fg="$3" dir_bg="$4" dir_fg="$5"
    local git_clean_bg="$6" git_clean_fg="$7" git_dirty_bg="$8" git_dirty_fg="$9"
    local char_color="${10}" err_color="${11:-196}"

    print ""
    print "  ${BOLD}${label}${NC}"
    print ""

    # With error status + clean git
    print -n "  $(bg256 $status_bg)$(fg256 $status_fg) ${CROSS} ${NC}$(fg256 $status_bg)$(bg256 $dir_bg)${SEP}${NC}"
    print -n "$(bg256 $dir_bg)$(fg256 $dir_fg) ~/Projects/my-app ${NC}$(fg256 $dir_bg)$(bg256 $git_clean_bg)${SEP}${NC}"
    print    "$(bg256 $git_clean_bg)$(fg256 $git_clean_fg) ${BRANCH} main ${STAGED} ${NC}$(fg256 $git_clean_bg)${SEP}${NC}  (clean)"

    # No status + dirty git
    print -n "  $(bg256 $dir_bg)$(fg256 $dir_fg) ~/Projects/my-app ${NC}$(fg256 $dir_bg)$(bg256 $git_dirty_bg)${SEP}${NC}"
    print    "$(bg256 $git_dirty_bg)$(fg256 $git_dirty_fg) ${BRANCH} feature/auth ${PLUSMINUS} ${NC}$(fg256 $git_dirty_bg)${SEP}${NC}  (dirty)"

    print "  $(fg256 $char_color)${CHEVRON}${NC} ls -la"
    print "  $(fg256 $err_color)${CHEVRON}${NC} (after error)"
    print ""
}

show_palette() {
    print ""
    print "  ${BOLD}256 Color Palette${NC}"
    print "  Use these numbers with: theme_preview.sh custom DIR_BG DIR_FG CLEAN_BG CLEAN_FG DIRTY_BG DIRTY_FG STATUS_BG STATUS_FG CHAR_COLOR"
    print ""

    # Standard 0-15
    print -n "  "
    for i in {0..15}; do
        print -n "$(bg256 $i)"
        printf " %3s " "$i"
        print -n "${NC}"
        [[ $i -eq 7 ]] && print "" && print -n "  "
    done
    print ""
    print ""

    # 216 colors (16-231)
    for row in {0..5}; do
        print -n "  "
        for green in {0..5}; do
            for blue in {0..5}; do
                local c=$((16 + row * 36 + green * 6 + blue))
                print -n "$(bg256 $c)"
                printf " %3s " "$c"
                print -n "${NC}"
            done
            print -n " "
        done
        print ""
    done
    print ""

    # Grayscale 232-255
    print -n "  "
    for i in {232..243}; do
        print -n "$(bg256 $i)$(fg256 255)"
        printf " %3s " "$i"
        print -n "${NC}"
    done
    print ""
    print -n "  "
    for i in {244..255}; do
        print -n "$(bg256 $i)$(fg256 0)"
        printf " %3s " "$i"
        print -n "${NC}"
    done
    print ""
    print ""
}

show_presets() {
    print ""
    print "  ${BOLD}=== Prompt Theme Previews ===${NC}"

    #                          label                    stat_bg stat_fg dir_bg dir_fg clean_bg clean_fg dirty_bg dirty_fg char  err
    render_prompt "Purple + Cyan (current)"              54      255     135    255    44       0        37       0       135   196
    render_prompt "Catppuccin Mocha"                      59      255     183    0      115      0        222      0       183   196
    render_prompt "Dracula"                               60      255     141    0      84       0        215      0       141   196
    render_prompt "Nord"                                  60      255     67     255    72       0        179      0       67    196
    render_prompt "Tokyo Night"                           60      255     111    0      79       0        173      0       111   196
    render_prompt "Gruvbox"                               237     223     130    235    107      235      172      235     130   196
    render_prompt "Rose Pine"                             53      255     168    0      108      0        173      0       168   196
    render_prompt "Cyberpunk"                             201     0       51     255    46       0        226      0       51    196
    render_prompt "Ocean"                                 24      255     32     255    43       0        38       255     32    196
    render_prompt "Sunset"                                52      255     208    0      220      0        196      255     208   196
    render_prompt "Monochrome"                            238     255     245    0      250      0        243      255     245   196
}

case "${1:-presets}" in
    pick|palette|colors)
        show_palette
        ;;
    custom)
        shift
        if [[ $# -lt 9 ]]; then
            print "Usage: $0 custom DIR_BG DIR_FG CLEAN_BG CLEAN_FG DIRTY_BG DIRTY_FG STATUS_BG STATUS_FG CHAR_COLOR"
            print "Example: $0 custom 135 255 44 0 37 0 54 255 135"
            exit 1
        fi
        render_prompt "Custom: dir=$1/$2 clean=$3/$4 dirty=$5/$6 status=$7/$8 char=$9" \
            "$7" "$8" "$1" "$2" "$3" "$4" "$5" "$6" "$9" "${10:-196}"
        ;;
    *)
        show_presets
        print ""
        print "  ${BOLD}Usage:${NC}"
        print "    ${0:t}              Show all preset themes"
        print "    ${0:t} palette      Show 256-color picker"
        print "    ${0:t} custom DIR_BG DIR_FG CLEAN_BG CLEAN_FG DIRTY_BG DIRTY_FG STATUS_BG STATUS_FG CHAR [ERR]"
        print ""
        print "  Example: ${0:t} custom 135 255 44 0 37 0 54 255 135"
        print ""
        ;;
esac
