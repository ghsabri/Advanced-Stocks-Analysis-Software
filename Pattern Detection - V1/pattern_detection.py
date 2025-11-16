"""
Pattern Detection Module for TR Chart Generator v4.0

Detects TOP 8 most useful chart patterns:
1. Head & Shoulders (bearish reversal)
2. Inverse Head & Shoulders (bullish reversal)
3. Double Top (bearish)
4. Double Bottom (bullish)
5. Ascending Triangle (bullish continuation)
6. Descending Triangle (bearish continuation)
7. Symmetrical Triangle (neutral)
8. Cup & Handle (bullish)
"""

import pandas as pd
import numpy as np
from scipy.signal import find_peaks


class PatternDetector:
    """Detects the top 8 chart patterns"""
    
    def __init__(self, df, price_col='Close'):
        self.df = df.copy()
        self.price_col = price_col
        
        # Find price column
        if price_col not in df.columns:
            for col in ['Close', 'close', 'adjClose', 'adj_close']:
                if col in df.columns:
                    self.price_col = col
                    break
        
        self.prices = df[self.price_col].values
        self.dates = df.index
        self._find_peaks_and_troughs()
    
    def _find_peaks_and_troughs(self):
        """Find significant peaks and troughs"""
        distance = max(5, len(self.prices) // 50)
        prominence = np.std(self.prices) * 0.5
        
        peaks, _ = find_peaks(self.prices, distance=distance, prominence=prominence)
        troughs, _ = find_peaks(-self.prices, distance=distance, prominence=prominence)
        
        self.peaks = peaks
        self.troughs = troughs
    
    def detect_all_patterns(self):
        """Detect all 8 patterns"""
        patterns = []
        
        print("🔍 Detecting patterns...")
        
        hs = self.detect_head_and_shoulders()
        patterns.extend(hs)
        print(f"   Found {len(hs)} Head & Shoulders")
        
        ihs = self.detect_inverse_head_and_shoulders()
        patterns.extend(ihs)
        print(f"   Found {len(ihs)} Inverse H&S")
        
        dt = self.detect_double_top()
        patterns.extend(dt)
        print(f"   Found {len(dt)} Double Tops")
        
        db = self.detect_double_bottom()
        patterns.extend(db)
        print(f"   Found {len(db)} Double Bottoms")
        
        at = self.detect_ascending_triangle()
        patterns.extend(at)
        print(f"   Found {len(at)} Ascending Triangles")
        
        dtr = self.detect_descending_triangle()
        patterns.extend(dtr)
        print(f"   Found {len(dtr)} Descending Triangles")
        
        st = self.detect_symmetrical_triangle()
        patterns.extend(st)
        print(f"   Found {len(st)} Symmetrical Triangles")
        
        ch = self.detect_cup_and_handle()
        patterns.extend(ch)
        print(f"   Found {len(ch)} Cup & Handles")
        
        print(f"✅ Total: {len(patterns)} patterns\n")
        
        patterns.sort(key=lambda x: x['start_date'])
        return patterns
    
    def detect_head_and_shoulders(self):
        """Head & Shoulders (bearish reversal)"""
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
            
            # Head must be highest
            if head <= left or head <= right:
                continue
            
            if head < left * 1.03 or head < right * 1.03:
                continue
            
            # Shoulders roughly equal
            shoulder_diff = abs(left - right) / left
            if shoulder_diff > 0.08:
                continue
            
            # Find troughs (neckline)
            between_lh = self.troughs[(self.troughs > left_idx) & (self.troughs < head_idx)]
            between_hr = self.troughs[(self.troughs > head_idx) & (self.troughs < right_idx)]
            
            if len(between_lh) == 0 or len(between_hr) == 0:
                continue
            
            left_trough = self.prices[between_lh[0]]
            right_trough = self.prices[between_hr[0]]
            neckline = (left_trough + right_trough) / 2
            
            height = head - neckline
            target = neckline - height
            
            confidence = int(min(95, 70 + (1 - shoulder_diff) * 25))
            
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
                'key_points': [(self.dates[left_idx], left), 
                              (self.dates[head_idx], head), 
                              (self.dates[right_idx], right)]
            })
        
        return patterns
    
    def detect_inverse_head_and_shoulders(self):
        """Inverse H&S (bullish reversal)"""
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
            
            # Head must be lowest
            if head >= left or head >= right:
                continue
            
            if head > left * 0.97 or head > right * 0.97:
                continue
            
            shoulder_diff = abs(left - right) / left
            if shoulder_diff > 0.08:
                continue
            
            # Find peaks (neckline)
            between_lh = self.peaks[(self.peaks > left_idx) & (self.peaks < head_idx)]
            between_hr = self.peaks[(self.peaks > head_idx) & (self.peaks < right_idx)]
            
            if len(between_lh) == 0 or len(between_hr) == 0:
                continue
            
            left_peak = self.prices[between_lh[0]]
            right_peak = self.prices[between_hr[0]]
            neckline = (left_peak + right_peak) / 2
            
            height = neckline - head
            target = neckline + height
            
            confidence = int(min(95, 70 + (1 - shoulder_diff) * 25))
            
            patterns.append({
                'type': 'Inverse H&S',
                'direction': 'bullish',
                'confidence': confidence,
                'start_date': self.dates[left_idx],
                'end_date': self.dates[right_idx],
                'start_idx': left_idx,
                'end_idx': right_idx,
                'neckline': neckline,
                'target_price': target,
                'key_points': [(self.dates[left_idx], left),
                              (self.dates[head_idx], head),
                              (self.dates[right_idx], right)]
            })
        
        return patterns
    
    def detect_double_top(self):
        """Double Top (bearish)"""
        patterns = []
        
        if len(self.peaks) < 2:
            return patterns
        
        for i in range(len(self.peaks) - 1):
            first_idx = self.peaks[i]
            second_idx = self.peaks[i + 1]
            
            first = self.prices[first_idx]
            second = self.prices[second_idx]
            
            # Peaks roughly equal
            diff = abs(first - second) / first
            if diff > 0.03:
                continue
            
            # Find trough between
            between = self.troughs[(self.troughs > first_idx) & (self.troughs < second_idx)]
            if len(between) == 0:
                continue
            
            trough = self.prices[between[0]]
            
            if trough > first * 0.95:
                continue
            
            height = first - trough
            target = trough - height
            confidence = int(min(90, 70 + (1 - diff) * 20))
            
            patterns.append({
                'type': 'Double Top',
                'direction': 'bearish',
                'confidence': confidence,
                'start_date': self.dates[first_idx],
                'end_date': self.dates[second_idx],
                'start_idx': first_idx,
                'end_idx': second_idx,
                'support': trough,
                'target_price': target,
                'key_points': [(self.dates[first_idx], first),
                              (self.dates[between[0]], trough),
                              (self.dates[second_idx], second)]
            })
        
        return patterns
    
    def detect_double_bottom(self):
        """Double Bottom (bullish)"""
        patterns = []
        
        if len(self.troughs) < 2:
            return patterns
        
        for i in range(len(self.troughs) - 1):
            first_idx = self.troughs[i]
            second_idx = self.troughs[i + 1]
            
            first = self.prices[first_idx]
            second = self.prices[second_idx]
            
            diff = abs(first - second) / first
            if diff > 0.03:
                continue
            
            between = self.peaks[(self.peaks > first_idx) & (self.peaks < second_idx)]
            if len(between) == 0:
                continue
            
            peak = self.prices[between[0]]
            
            if peak < first * 1.05:
                continue
            
            height = peak - first
            target = peak + height
            confidence = int(min(90, 70 + (1 - diff) * 20))
            
            patterns.append({
                'type': 'Double Bottom',
                'direction': 'bullish',
                'confidence': confidence,
                'start_date': self.dates[first_idx],
                'end_date': self.dates[second_idx],
                'start_idx': first_idx,
                'end_idx': second_idx,
                'resistance': peak,
                'target_price': target,
                'key_points': [(self.dates[first_idx], first),
                              (self.dates[between[0]], peak),
                              (self.dates[second_idx], second)]
            })
        
        return patterns
    
    def detect_ascending_triangle(self):
        """Ascending Triangle (bullish continuation)"""
        patterns = []
        
        min_bars = 30
        window_size = min(100, len(self.prices) // 2)
        
        for start in range(0, len(self.prices) - min_bars, 15):
            end = min(start + window_size, len(self.prices))
            window = self.prices[start:end]
            
            if len(window) < min_bars:
                continue
            
            # Find local peaks/troughs
            local_peaks = []
            local_troughs = []
            
            for i in range(2, len(window) - 2):
                if window[i] > window[i-1] and window[i] > window[i+1]:
                    local_peaks.append((start + i, window[i]))
                if window[i] < window[i-1] and window[i] < window[i+1]:
                    local_troughs.append((start + i, window[i]))
            
            if len(local_peaks) < 2 or len(local_troughs) < 2:
                continue
            
            # Flat resistance check
            peak_prices = [p[1] for p in local_peaks]
            peak_std = np.std(peak_prices)
            peak_mean = np.mean(peak_prices)
            
            if peak_std / peak_mean > 0.02:
                continue
            
            # Rising support check
            trough_indices = [t[0] for t in local_troughs]
            trough_prices = [t[1] for t in local_troughs]
            
            if len(trough_indices) < 2:
                continue
            
            slope = np.polyfit(trough_indices, trough_prices, 1)[0]
            
            if slope <= 0:
                continue
            
            height = peak_mean - trough_prices[0]
            target = peak_mean + height
            confidence = int(min(85, 65 + (slope / peak_mean) * 500))
            
            patterns.append({
                'type': 'Ascending Triangle',
                'direction': 'bullish',
                'confidence': confidence,
                'start_date': self.dates[start],
                'end_date': self.dates[end-1],
                'start_idx': start,
                'end_idx': end-1,
                'resistance': peak_mean,
                'target_price': target,
                'key_points': local_peaks + local_troughs
            })
        
        return patterns
    
    def detect_descending_triangle(self):
        """Descending Triangle (bearish continuation)"""
        patterns = []
        
        min_bars = 30
        window_size = min(100, len(self.prices) // 2)
        
        for start in range(0, len(self.prices) - min_bars, 15):
            end = min(start + window_size, len(self.prices))
            window = self.prices[start:end]
            
            if len(window) < min_bars:
                continue
            
            local_peaks = []
            local_troughs = []
            
            for i in range(2, len(window) - 2):
                if window[i] > window[i-1] and window[i] > window[i+1]:
                    local_peaks.append((start + i, window[i]))
                if window[i] < window[i-1] and window[i] < window[i+1]:
                    local_troughs.append((start + i, window[i]))
            
            if len(local_peaks) < 2 or len(local_troughs) < 2:
                continue
            
            # Flat support
            trough_prices = [t[1] for t in local_troughs]
            trough_std = np.std(trough_prices)
            trough_mean = np.mean(trough_prices)
            
            if trough_std / trough_mean > 0.02:
                continue
            
            # Falling resistance
            peak_indices = [p[0] for p in local_peaks]
            peak_prices = [p[1] for p in local_peaks]
            
            if len(peak_indices) < 2:
                continue
            
            slope = np.polyfit(peak_indices, peak_prices, 1)[0]
            
            if slope >= 0:
                continue
            
            height = peak_prices[0] - trough_mean
            target = trough_mean - height
            confidence = int(min(85, 65 + abs(slope / trough_mean) * 500))
            
            patterns.append({
                'type': 'Descending Triangle',
                'direction': 'bearish',
                'confidence': confidence,
                'start_date': self.dates[start],
                'end_date': self.dates[end-1],
                'start_idx': start,
                'end_idx': end-1,
                'support': trough_mean,
                'target_price': target,
                'key_points': local_peaks + local_troughs
            })
        
        return patterns
    
    def detect_symmetrical_triangle(self):
        """Symmetrical Triangle (neutral)"""
        patterns = []
        
        min_bars = 30
        window_size = min(100, len(self.prices) // 2)
        
        for start in range(0, len(self.prices) - min_bars, 15):
            end = min(start + window_size, len(self.prices))
            window = self.prices[start:end]
            
            if len(window) < min_bars:
                continue
            
            local_peaks = []
            local_troughs = []
            
            for i in range(2, len(window) - 2):
                if window[i] > window[i-1] and window[i] > window[i+1]:
                    local_peaks.append((start + i, window[i]))
                if window[i] < window[i-1] and window[i] < window[i+1]:
                    local_troughs.append((start + i, window[i]))
            
            if len(local_peaks) < 2 or len(local_troughs) < 2:
                continue
            
            peak_indices = [p[0] for p in local_peaks]
            peak_prices = [p[1] for p in local_peaks]
            peak_slope = np.polyfit(peak_indices, peak_prices, 1)[0]
            
            trough_indices = [t[0] for t in local_troughs]
            trough_prices = [t[1] for t in local_troughs]
            trough_slope = np.polyfit(trough_indices, trough_prices, 1)[0]
            
            # Converging: peaks falling, troughs rising
            if peak_slope >= 0 or trough_slope <= 0:
                continue
            
            # Similar slopes (converging)
            if abs(peak_slope) < abs(trough_slope) * 0.5 or abs(peak_slope) > abs(trough_slope) * 2:
                continue
            
            height = (peak_prices[0] - trough_prices[0]) / 2
            target = window[-1] + height
            confidence = int(min(80, 60 + abs(peak_slope + trough_slope) * 300))
            
            patterns.append({
                'type': 'Symmetrical Triangle',
                'direction': 'neutral',
                'confidence': confidence,
                'start_date': self.dates[start],
                'end_date': self.dates[end-1],
                'start_idx': start,
                'end_idx': end-1,
                'target_price': target,
                'key_points': local_peaks + local_troughs
            })
        
        return patterns
    
    def detect_cup_and_handle(self):
        """Cup & Handle (bullish)"""
        patterns = []
        
        min_bars = 50
        
        if len(self.prices) < min_bars:
            return patterns
        
        for start in range(0, len(self.prices) - min_bars, 20):
            end = min(start + min_bars * 2, len(self.prices))
            window = self.prices[start:end]
            
            if len(window) < min_bars:
                continue
            
            # Cup: U-shape
            cup_start = window[0]
            cup_low_idx = np.argmin(window[:len(window)//2])
            cup_low = window[cup_low_idx]
            
            # 10% drop minimum
            if cup_low > cup_start * 0.90:
                continue
            
            # Recovery
            recovery_idx = None
            for i in range(cup_low_idx + 5, len(window)):
                if window[i] >= cup_start * 0.95:
                    recovery_idx = i
                    break
            
            if recovery_idx is None:
                continue
            
            # Handle
            handle_start = recovery_idx
            handle_end = min(handle_start + 20, len(window))
            
            if handle_end >= len(window):
                continue
            
            handle = window[handle_start:handle_end]
            handle_low = np.min(handle)
            
            # Small pullback 3-12%
            pullback = (window[handle_start] - handle_low) / window[handle_start]
            if pullback < 0.03 or pullback > 0.12:
                continue
            
            depth = cup_start - cup_low
            target = cup_start + depth
            confidence = int(min(85, 65 + (depth / cup_start) * 50))
            
            patterns.append({
                'type': 'Cup & Handle',
                'direction': 'bullish',
                'confidence': confidence,
                'start_date': self.dates[start],
                'end_date': self.dates[start + handle_end - 1],
                'start_idx': start,
                'end_idx': start + handle_end - 1,
                'target_price': target,
                'key_points': [(self.dates[start], cup_start),
                              (self.dates[start + cup_low_idx], cup_low),
                              (self.dates[start + recovery_idx], window[recovery_idx])]
            })
        
        return patterns


def detect_patterns_for_chart(df, price_col='Close'):
    """Detect patterns for chart display"""
    detector = PatternDetector(df, price_col)
    return detector.detect_all_patterns()
