"""
Pattern Curves Module - Clean Version
=====================================
Draws smooth curves overlaid on patterns WITHOUT cluttering the chart.
- No extra legend entries
- BP markers positioned correctly on chart
- Clean, professional appearance
"""

import numpy as np
import plotly.graph_objects as go

try:
    from scipy.interpolate import CubicSpline
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


def generate_smooth_curve(x_points, y_points, num_points=30):
    """Generate smooth curve through given points."""
    if len(x_points) < 2:
        return np.array(x_points), np.array(y_points)
    
    x = np.array(x_points, dtype=float)
    y = np.array(y_points, dtype=float)
    
    sort_idx = np.argsort(x)
    x = x[sort_idx]
    y = y[sort_idx]
    
    unique_mask = np.diff(x, prepend=x[0]-1) > 0
    x = x[unique_mask]
    y = y[unique_mask]
    
    if len(x) < 2:
        return x, y
    
    try:
        x_smooth = np.linspace(x.min(), x.max(), num_points)
        
        if SCIPY_AVAILABLE and len(x) >= 3:
            spline = CubicSpline(x, y)
            y_smooth = spline(x_smooth)
        else:
            y_smooth = np.interp(x_smooth, x, y)
        
        return x_smooth, y_smooth
    except:
        return x, y


def add_pattern_curves_to_chart(fig, patterns, df, show_bp=True):
    """
    Add smooth pattern curves to chart - clean version.
    """
    if 'Date' in df.columns:
        dates = df['Date'].values
    else:
        dates = df.index.values
    
    prices = df['Close'].values
    curves_added = 0
    
    for pattern in patterns:
        try:
            pattern_type = pattern['type']
            start_idx = pattern['start_idx']
            end_idx = pattern['end_idx']
            key_points = pattern.get('key_points', [])
            
            # Curve color - contrasting with price lines
            if pattern['direction'] == 'bullish':
                curve_color = 'blue'
            elif pattern['direction'] == 'bearish':
                curve_color = 'darkmagenta'
            else:
                curve_color = 'darkorange'
            
            x_curve = None
            y_curve = None
            
            # Generate curve based on pattern type
            if pattern_type == 'Cup & Handle' and len(key_points) >= 3:
                left_price = key_points[0][1]
                bottom_price = key_points[1][1]
                right_price = key_points[2][1]
                
                cup_bottom_idx = start_idx + int((end_idx - start_idx) * 0.4)
                recovery_idx = start_idx + int((end_idx - start_idx) * 0.75)
                
                x_pts = [start_idx, cup_bottom_idx, recovery_idx, end_idx]
                y_pts = [left_price, bottom_price, right_price, right_price * 0.98]
                
                x_curve, y_curve = generate_smooth_curve(x_pts, y_pts)
            
            elif pattern_type == 'Double Bottom' and len(key_points) >= 3:
                trough1_price = key_points[0][1]
                peak_price = key_points[1][1]
                trough2_price = key_points[2][1]
                
                mid_idx = (start_idx + end_idx) // 2
                x_pts = [start_idx, mid_idx, end_idx]
                y_pts = [trough1_price, peak_price, trough2_price]
                
                x_curve, y_curve = generate_smooth_curve(x_pts, y_pts)
            
            elif pattern_type == 'Double Top' and len(key_points) >= 3:
                peak1_price = key_points[0][1]
                trough_price = key_points[1][1]
                peak2_price = key_points[2][1]
                
                mid_idx = (start_idx + end_idx) // 2
                x_pts = [start_idx, mid_idx, end_idx]
                y_pts = [peak1_price, trough_price, peak2_price]
                
                x_curve, y_curve = generate_smooth_curve(x_pts, y_pts)
            
            elif pattern_type == 'Head & Shoulders' and len(key_points) >= 3:
                left_price = key_points[0][1]
                head_price = key_points[1][1]
                right_price = key_points[2][1]
                
                neckline = (left_price + right_price) / 2 * 0.97
                quarter = (end_idx - start_idx) // 4
                
                x_pts = [start_idx, start_idx + quarter, start_idx + 2*quarter,
                         start_idx + 3*quarter, end_idx]
                y_pts = [neckline, left_price, head_price, right_price, neckline]
                
                x_curve, y_curve = generate_smooth_curve(x_pts, y_pts, num_points=40)
            
            elif pattern_type == 'Inverse Head & Shoulders' and len(key_points) >= 3:
                left_price = key_points[0][1]
                head_price = key_points[1][1]
                right_price = key_points[2][1]
                
                neckline = (left_price + right_price) / 2 * 1.03
                quarter = (end_idx - start_idx) // 4
                
                x_pts = [start_idx, start_idx + quarter, start_idx + 2*quarter,
                         start_idx + 3*quarter, end_idx]
                y_pts = [neckline, left_price, head_price, right_price, neckline]
                
                x_curve, y_curve = generate_smooth_curve(x_pts, y_pts, num_points=40)
            
            # Skip triangles for now - trendlines handled by original code
            elif 'Triangle' in pattern_type:
                continue
            
            # Add curve as scatter trace - NO LEGEND
            if x_curve is not None and y_curve is not None and len(x_curve) > 1:
                x_curve_int = np.clip(x_curve, 0, len(dates) - 1).astype(int)
                x_dates = [dates[i] for i in x_curve_int]
                
                fig.add_trace(go.Scatter(
                    x=x_dates,
                    y=y_curve,
                    mode='lines',
                    line=dict(color=curve_color, width=4, dash='dot'),
                    hoverinfo='skip',  # Don't show hover for curves
                    showlegend=False   # NO LEGEND ENTRY
                ))
                
                curves_added += 1
                print(f"  ✓ {pattern_type} curve added")
        
        except Exception as e:
            print(f"  ✗ Error {pattern.get('type', '?')}: {e}")
    
    print(f"✅ {curves_added} pattern curves added (no legend clutter)")
    return fig


if __name__ == '__main__':
    print("Pattern Curves - Clean Version")
