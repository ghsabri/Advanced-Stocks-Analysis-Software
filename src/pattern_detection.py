"""
Pattern Detection Module - Top 8 Chart Patterns
FIXED: Proper datetime handling
"""

import pandas as pd
import numpy as np
from scipy.signal import find_peaks


class PatternDetector:
    """Detects chart patterns in price data"""
    
    def __init__(self, df, price_col='Close'):
        """Initialize with price data"""
        self.df = df.copy()
        
        # Find price column
        if price_col in df.columns:
            self.price_col = price_col
        elif 'Close' in df.columns:
            self.price_col = 'Close'
        elif 'adjClose' in df.columns:
            self.price_col = 'adjClose'
        else:
            raise ValueError("No price column found")
        
        self.prices = df[self.price_col].values
        
        # Get dates - ensure datetime format
        if 'Date' in df.columns:
            self.dates = pd.to_datetime(df['Date']).reset_index(drop=True)
        else:
            self.dates = pd.to_datetime(df.index).to_series().reset_index(drop=True)
        
        self._find_peaks_and_troughs()
    
    def _find_peaks_and_troughs(self):
        """Find significant peaks and troughs"""
        distance = max(5, len(self.prices) // 50)
        prominence = np.std(self.prices) * 0.3
        
        peaks, _ = find_peaks(self.prices, distance=distance, prominence=prominence)
        troughs, _ = find_peaks(-self.prices, distance=distance, prominence=prominence)
        
        self.peaks = peaks
        self.troughs = troughs
    
    def detect_all_patterns(self):
        """Detect all 8 patterns and return list"""
        patterns = []
        
        patterns.extend(self.detect_head_and_shoulders())
        patterns.extend(self.detect_inverse_head_and_shoulders())
        patterns.extend(self.detect_double_top())
        patterns.extend(self.detect_double_bottom())
        patterns.extend(self.detect_ascending_triangle())
        patterns.extend(self.detect_descending_triangle())
        patterns.extend(self.detect_symmetrical_triangle())
        patterns.extend(self.detect_cup_and_handle())
        
        patterns.sort(key=lambda x: x['start_date'])
        return patterns
    
    def detect_head_and_shoulders(self):
        """Bearish reversal pattern"""
        patterns = []
        if len(self.peaks) < 3:
            return patterns
        
        for i in range(len(self.peaks) - 2):
            left_idx = self.peaks[i]
            head_idx = self.peaks[i + 1]
            right_idx = self.peaks[i + 2]
            
            left = self.prices[left_idx]
            head = self.prices[head_idx]
            right = self.prices[right_idx]
            
            if head <= max(left, right) * 1.02:
                continue
            
            if abs(left - right) / max(left, right) > 0.05:
                continue
            
            neckline = (left + right) / 2
            target = neckline - (head - neckline)
            confidence = min(85, int(60 + (head - neckline) / head * 100))
            
            patterns.append({
                'type': 'Head & Shoulders',
                'direction': 'bearish',
                'confidence': confidence,
                'start_date': self.dates[left_idx],
                'end_date': self.dates[right_idx],
                'start_idx': left_idx,
                'end_idx': right_idx,
                'neckline': neckline,
                'target_price': target,
                'key_points': [
                    (self.dates[left_idx], left),
                    (self.dates[head_idx], head),
                    (self.dates[right_idx], right)
                ]
            })
        
        return patterns
    
    def detect_inverse_head_and_shoulders(self):
        """Bullish reversal pattern"""
        patterns = []
        if len(self.troughs) < 3:
            return patterns
        
        for i in range(len(self.troughs) - 2):
            left_idx = self.troughs[i]
            head_idx = self.troughs[i + 1]
            right_idx = self.troughs[i + 2]
            
            left = self.prices[left_idx]
            head = self.prices[head_idx]
            right = self.prices[right_idx]
            
            if head >= min(left, right) * 0.98:
                continue
            
            if abs(left - right) / min(left, right) > 0.05:
                continue
            
            neckline = (left + right) / 2
            target = neckline + (neckline - head)
            confidence = min(85, int(60 + (neckline - head) / neckline * 100))
            
            patterns.append({
                'type': 'Inverse Head & Shoulders',
                'direction': 'bullish',
                'confidence': confidence,
                'start_date': self.dates[left_idx],
                'end_date': self.dates[right_idx],
                'start_idx': left_idx,
                'end_idx': right_idx,
                'neckline': neckline,
                'target_price': target,
                'key_points': [
                    (self.dates[left_idx], left),
                    (self.dates[head_idx], head),
                    (self.dates[right_idx], right)
                ]
            })
        
        return patterns
    
    def detect_double_top(self):
        """Bearish reversal - two peaks at same level"""
        patterns = []
        if len(self.peaks) < 2:
            return patterns
        
        for i in range(len(self.peaks) - 1):
            peak1_idx = self.peaks[i]
            peak2_idx = self.peaks[i + 1]
            
            peak1 = self.prices[peak1_idx]
            peak2 = self.prices[peak2_idx]
            
            if abs(peak1 - peak2) / max(peak1, peak2) > 0.02:
                continue
            
            between = self.troughs[(self.troughs > peak1_idx) & (self.troughs < peak2_idx)]
            if len(between) == 0:
                continue
            
            trough_idx = between[0]
            trough = self.prices[trough_idx]
            
            target = trough - (peak1 - trough)
            confidence = min(80, int(55 + (peak1 - trough) / peak1 * 100))
            
            patterns.append({
                'type': 'Double Top',
                'direction': 'bearish',
                'confidence': confidence,
                'start_date': self.dates[peak1_idx],
                'end_date': self.dates[peak2_idx],
                'start_idx': peak1_idx,
                'end_idx': peak2_idx,
                'support': trough,
                'target_price': target,
                'key_points': [
                    (self.dates[peak1_idx], peak1),
                    (self.dates[trough_idx], trough),
                    (self.dates[peak2_idx], peak2)
                ]
            })
        
        return patterns
    
    def detect_double_bottom(self):
        """Bullish reversal - two troughs at same level"""
        patterns = []
        if len(self.troughs) < 2:
            return patterns
        
        for i in range(len(self.troughs) - 1):
            trough1_idx = self.troughs[i]
            trough2_idx = self.troughs[i + 1]
            
            trough1 = self.prices[trough1_idx]
            trough2 = self.prices[trough2_idx]
            
            if abs(trough1 - trough2) / min(trough1, trough2) > 0.02:
                continue
            
            between = self.peaks[(self.peaks > trough1_idx) & (self.peaks < trough2_idx)]
            if len(between) == 0:
                continue
            
            peak_idx = between[0]
            peak = self.prices[peak_idx]
            
            target = peak + (peak - trough1)
            confidence = min(80, int(55 + (peak - trough1) / peak * 100))
            
            patterns.append({
                'type': 'Double Bottom',
                'direction': 'bullish',
                'confidence': confidence,
                'start_date': self.dates[trough1_idx],
                'end_date': self.dates[trough2_idx],
                'start_idx': trough1_idx,
                'end_idx': trough2_idx,
                'resistance': peak,
                'target_price': target,
                'key_points': [
                    (self.dates[trough1_idx], trough1),
                    (self.dates[peak_idx], peak),
                    (self.dates[trough2_idx], trough2)
                ]
            })
        
        return patterns
    
    def detect_ascending_triangle(self):
        """Bullish continuation - flat top, rising bottom"""
        patterns = []
        window_size = 30
        
        for start in range(0, len(self.prices) - window_size, 10):
            window = self.prices[start:start + window_size]
            
            local_peaks = [i for i in self.peaks if start <= i < start + window_size]
            local_troughs = [i for i in self.troughs if start <= i < start + window_size]
            
            if len(local_peaks) < 2 or len(local_troughs) < 2:
                continue
            
            peak_prices = [self.prices[i] for i in local_peaks]
            if max(peak_prices) - min(peak_prices) > np.mean(peak_prices) * 0.03:
                continue
            
            trough_prices = [self.prices[i] for i in local_troughs]
            if trough_prices[-1] <= trough_prices[0]:
                continue
            
            resistance = np.mean(peak_prices)
            target = resistance + (resistance - trough_prices[0])
            confidence = min(75, int(50 + len(local_peaks) * 10))
            
            patterns.append({
                'type': 'Ascending Triangle',
                'direction': 'bullish',
                'confidence': confidence,
                'start_date': self.dates[start],
                'end_date': self.dates[start + window_size - 1],
                'start_idx': start,
                'end_idx': start + window_size - 1,
                'resistance': resistance,
                'target_price': target,
                'key_points': [(self.dates[i], self.prices[i]) for i in local_peaks]
            })
        
        return patterns
    
    def detect_descending_triangle(self):
        """Bearish continuation - flat bottom, falling top"""
        patterns = []
        window_size = 30
        
        for start in range(0, len(self.prices) - window_size, 10):
            window = self.prices[start:start + window_size]
            
            local_peaks = [i for i in self.peaks if start <= i < start + window_size]
            local_troughs = [i for i in self.troughs if start <= i < start + window_size]
            
            if len(local_peaks) < 2 or len(local_troughs) < 2:
                continue
            
            trough_prices = [self.prices[i] for i in local_troughs]
            if max(trough_prices) - min(trough_prices) > np.mean(trough_prices) * 0.03:
                continue
            
            peak_prices = [self.prices[i] for i in local_peaks]
            if peak_prices[-1] >= peak_prices[0]:
                continue
            
            support = np.mean(trough_prices)
            target = support - (peak_prices[0] - support)
            confidence = min(75, int(50 + len(local_troughs) * 10))
            
            patterns.append({
                'type': 'Descending Triangle',
                'direction': 'bearish',
                'confidence': confidence,
                'start_date': self.dates[start],
                'end_date': self.dates[start + window_size - 1],
                'start_idx': start,
                'end_idx': start + window_size - 1,
                'support': support,
                'target_price': target,
                'key_points': [(self.dates[i], self.prices[i]) for i in local_troughs]
            })
        
        return patterns
    
    def detect_symmetrical_triangle(self):
        """Neutral - converging highs and lows"""
        patterns = []
        window_size = 30
        
        for start in range(0, len(self.prices) - window_size, 10):
            local_peaks = [i for i in self.peaks if start <= i < start + window_size]
            local_troughs = [i for i in self.troughs if start <= i < start + window_size]
            
            if len(local_peaks) < 2 or len(local_troughs) < 2:
                continue
            
            peak_prices = [self.prices[i] for i in local_peaks]
            if peak_prices[-1] >= peak_prices[0] * 0.97:
                continue
            
            trough_prices = [self.prices[i] for i in local_troughs]
            if trough_prices[-1] <= trough_prices[0] * 1.03:
                continue
            
            apex = (peak_prices[-1] + trough_prices[-1]) / 2
            confidence = min(70, int(45 + (len(local_peaks) + len(local_troughs)) * 5))
            
            patterns.append({
                'type': 'Symmetrical Triangle',
                'direction': 'neutral',
                'confidence': confidence,
                'start_date': self.dates[start],
                'end_date': self.dates[start + window_size - 1],
                'start_idx': start,
                'end_idx': start + window_size - 1,
                'apex': apex,
                'target_price': None,
                'key_points': [(self.dates[i], self.prices[i]) for i in local_peaks + local_troughs]
            })
        
        return patterns
    
    def detect_cup_and_handle(self):
        """Bullish - U-shaped cup with small handle"""
        patterns = []
        window_size = 50
        
        for start in range(0, len(self.prices) - window_size, 10):
            window = self.prices[start:start + window_size]
            
            cup_low_idx = np.argmin(window[:40])
            cup_low = window[cup_low_idx]
            cup_start = window[0]
            
            if cup_low >= cup_start * 0.95:
                continue
            
            recovery_idx = cup_low_idx + np.argmax(window[cup_low_idx:40])
            if window[recovery_idx] < cup_start * 0.95:
                continue
            
            if recovery_idx + 10 >= len(window):
                continue
            
            handle = window[recovery_idx:recovery_idx + 10]
            handle_low = np.min(handle)
            
            pullback = (window[recovery_idx] - handle_low) / window[recovery_idx]
            if not (0.03 <= pullback <= 0.12):
                continue
            
            target = cup_start + (cup_start - cup_low)
            confidence = min(85, int(60 + (cup_start - cup_low) / cup_start * 100))
            
            patterns.append({
                'type': 'Cup & Handle',
                'direction': 'bullish',
                'confidence': confidence,
                'start_date': self.dates[start],
                'end_date': self.dates[start + recovery_idx + 10],
                'start_idx': start,
                'end_idx': start + recovery_idx + 10,
                'cup_depth': cup_low,
                'target_price': target,
                'key_points': [
                    (self.dates[start], cup_start),
                    (self.dates[start + cup_low_idx], cup_low),
                    (self.dates[start + recovery_idx], window[recovery_idx])
                ]
            })
        
        return patterns


def detect_patterns_for_chart(df, price_col='Close', remove_overlaps=True):
    """
    Main function to detect patterns
    
    Args:
        df: DataFrame with price data
        price_col: Column name for prices
        remove_overlaps: If True, remove overlapping patterns (default)
    
    Returns:
        List of detected patterns
    """
    detector = PatternDetector(df, price_col)
    all_patterns = detector.detect_all_patterns()
    
    if remove_overlaps:
        # Remove overlapping patterns - keep highest confidence
        non_overlapping = remove_overlapping_patterns(all_patterns)
        return non_overlapping
    else:
        # Return all patterns
        all_patterns.sort(key=lambda x: x['start_date'])
        return all_patterns


def remove_overlapping_patterns(patterns):
    """
    Remove overlapping patterns with SMART priority:
    1. ALWAYS keep Triangles (Ascending, Descending, Symmetrical) - they're important
    2. For others, keep MOST RECENT patterns first
    3. Then keep highest confidence
    
    This ensures important patterns like Ascending Triangle ALWAYS show up!
    """
    if not patterns:
        return patterns
    
    print(f"\n🔍 PATTERN FILTERING DEBUG:")
    print(f"Total patterns found: {len(patterns)}")
    
    # Separate triangles from other patterns
    triangles = [p for p in patterns if 'Triangle' in p['type']]
    others = [p for p in patterns if 'Triangle' not in p['type']]
    
    print(f"  Triangles: {len(triangles)}")
    for t in triangles:
        print(f"    - {t['type']}: {t['confidence']}% (idx {t['start_idx']}-{t['end_idx']})")
    
    print(f"  Others: {len(others)}")
    for o in others[:5]:  # Show first 5
        print(f"    - {o['type']}: {o['confidence']}% (idx {o['start_idx']}-{o['end_idx']})")
    
    # Sort others by: end_idx (most recent first), then confidence
    others_sorted = sorted(
        others, 
        key=lambda x: (x['end_idx'], x['confidence']), 
        reverse=True
    )
    
    # Start with ALL triangles - they're always kept!
    selected = triangles.copy()
    print(f"\n✅ Starting with {len(selected)} triangles (auto-selected)")
    
    # Now add other patterns if they don't overlap too much
    for pattern in others_sorted:
        p_start = pattern['start_idx']
        p_end = pattern['end_idx']
        
        # Check overlap with already selected patterns
        overlaps = False
        for selected_pattern in selected:
            s_start = selected_pattern['start_idx']
            s_end = selected_pattern['end_idx']
            
            # Calculate overlap
            overlap_start = max(p_start, s_start)
            overlap_end = min(p_end, s_end)
            
            if overlap_end > overlap_start:
                overlap_length = overlap_end - overlap_start
                p_length = p_end - p_start
                s_length = s_end - s_start
                
                # More lenient: 40% overlap threshold
                if (overlap_length / p_length > 0.4) or (overlap_length / s_length > 0.4):
                    overlaps = True
                    print(f"  ❌ {pattern['type']} overlaps with {selected_pattern['type']}")
                    break
        
        if not overlaps:
            selected.append(pattern)
            print(f"  ✅ {pattern['type']} added")
    
    print(f"\n📊 FINAL: {len(selected)} patterns selected")
    
    # Sort by date for display
    selected.sort(key=lambda x: x['start_date'])
    
    return selected
