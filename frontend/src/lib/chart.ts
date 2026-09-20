/** Shared dark-theme styling for recharts tooltips.
 *
 *  Both charts sit on the same near-black panel. Setting only `contentStyle`
 *  leaves recharts' own dark default text, which renders unreadably against
 *  it, so the three always belong together. Spread this onto a `<Tooltip>`
 *  rather than repeating them.
 */
export const TOOLTIP_STYLE = {
  contentStyle: {
    background: '#171717',
    border: '1px solid #404040',
    borderRadius: 8,
    fontSize: 12,
  },
  itemStyle: { color: '#e5e5e5' },
  labelStyle: { color: '#e5e5e5' },
}
