import React, { useState, useEffect } from 'react';
import './VolumeProfileOverlay.css';

import API_BASE from '../config';
import { formatPrice } from '../utils/currencyUtils';

/**
 * Volume Profile Overlay Component
 * 
 * Displays volume profile as an overlay on the right side of the price chart
 * Shows POC, VAH, VAL lines through the chart
 * 
 * IMPORTANT: For correct alignment, chartHeight and chartMargin MUST match
 * the Recharts ResponsiveContainer and ComposedChart settings exactly!
 * 
 * CALIBRATION: If bars still don't align perfectly, use heightAdjustment prop
 */
function VolumeProfileOverlay({ 
  stockId, 
  period = 30, 
  numBins = 50, 
  chartHeight = 400,
  chartMargin = { top: 10, right: 30, left: 0, bottom: 0 }, // Must match Recharts margin exactly
  heightAdjustment = 0, // Fine-tune vertical alignment (negative = compress, positive = stretch)
  priceRange = null, // { min, max } to match chart scale
  onProfileLoad = null 
}) {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!stockId) return;

    const fetchVolumeProfile = async () => {
      setLoading(true);

      try {
        const response = await fetch(
          `${API_BASE}/stock-data/${stockId}/volume-profile?period_days=${period}&num_bins=${numBins}`
        );

        if (response.ok) {
          const data = await response.json();
          
          if (!data.error) {
            setProfileData(data);
            
            if (onProfileLoad) {
              onProfileLoad({
                poc: data.poc,
                vah: data.value_area.high,
                val: data.value_area.low
              });
            }
          }
        }
      } catch (err) {
        console.error('Error fetching volume profile:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchVolumeProfile();
  }, [stockId, period, numBins, onProfileLoad]);

  // Separate useEffect to call onProfileLoad when data changes
  useEffect(() => {
    if (profileData && onProfileLoad) {
      onProfileLoad({
        poc: profileData.poc,
        vah: profileData.value_area.high,
        val: profileData.value_area.low
      });
    }
  }, [profileData, onProfileLoad]);

  if (loading || !profileData) {
    return null;
  }

  // Calculate bar heights and positions
  const minPrice = priceRange?.min || profileData.price_range.min;
  const maxPrice = priceRange?.max || profileData.price_range.max;
  const priceRangeValue = maxPrice - minPrice;
  
  // CRITICAL: Match Recharts' internal plotting area calculation
  // After extensive testing, Recharts with ResponsiveContainer effectively uses:
  // - The full container height MINUS the margins
  // - The XAxis is rendered WITHIN this area, not as additional space
  // So the plotting area for the chart lines is actually larger than we thought!
  //
  // The key insight: Recharts' YAxis domain maps to the ENTIRE ResponsiveContainer
  // minus only the explicit margins, NOT minus the XAxis height
  // 
  // Base calculation: effectiveHeight = chartHeight - chartMargin.top - chartMargin.bottom
  // Fine-tuning: Apply heightAdjustment for perfect alignment
  const baseHeight = chartHeight - chartMargin.top - chartMargin.bottom;
  const effectiveHeight = baseHeight + heightAdjustment;
  const topOffset = chartMargin.top;
  
  // Minimal debug output (enable for calibration)
  const DEBUG_MODE = false;
  
  if (DEBUG_MODE) {
    console.log('🎯 OVERLAY POSITIONING:');
    console.log('   chartHeight=' + chartHeight + ', margins=' + JSON.stringify(chartMargin));
    console.log('   baseHeight=' + baseHeight + 'px, heightAdjustment=' + heightAdjustment + 'px');
    console.log('   effectiveHeight=' + effectiveHeight + 'px, topOffset=' + topOffset + 'px');
    console.log('   💡 TIP: If bars are too HIGH, use negative heightAdjustment (e.g., -10)');
    console.log('   💡 TIP: If bars are too LOW, use positive heightAdjustment (e.g., +10)');
    console.log('   This should match Recharts internal plotting area!');
  }
  
  if (DEBUG_MODE) {
    // Debug logging
    console.log('=== Volume Profile Overlay Debug ===');
    console.log('Chart Settings:', {
      chartHeight,
      chartMargin,
      effectiveHeight,
      topOffset
    });
    console.log('Price Range (Chart):', {
      minPrice: minPrice.toFixed(2),
      maxPrice: maxPrice.toFixed(2),
      priceRangeValue: priceRangeValue.toFixed(2)
    });
    console.log('Price Range (Backend):', profileData.price_range);
    console.log('Key Levels:', {
      poc: profileData.poc.toFixed(2),
      vah: profileData.value_area.high.toFixed(2),
      val: profileData.value_area.low.toFixed(2)
    });
    console.log('Bins:', {
      binSize: profileData.bin_size.toFixed(2),
      numBins: profileData.price_levels.length,
      firstBinCenter: profileData.price_levels[0]?.toFixed(2),
      lastBinCenter: profileData.price_levels[profileData.price_levels.length - 1]?.toFixed(2)
    });
    
    // Calculate where POC should appear in pixels
    const pocYPosition = ((maxPrice - profileData.poc) / priceRangeValue) * effectiveHeight;
    const vahYPosition = ((maxPrice - profileData.value_area.high) / priceRangeValue) * effectiveHeight;
    const valYPosition = ((maxPrice - profileData.value_area.low) / priceRangeValue) * effectiveHeight;
    
    console.log('Expected Label Positions (px from top of effective area):', {
      poc: pocYPosition.toFixed(2) + 'px',
      vah: vahYPosition.toFixed(2) + 'px',
      val: valYPosition.toFixed(2) + 'px'
    });
    console.log('Label container will be positioned:', {
      top: topOffset + 'px',
      height: effectiveHeight + 'px'
    });
    console.log('===================================');
  }
  
  // Normalize volumes for display
  const maxVolume = Math.max(...profileData.volumes);
  
  // Create bars for display - using PIXEL values for precise alignment
  const bars = profileData.price_levels
    .map((price, index) => {
      const volume = profileData.volumes[index];
      
      // price_levels contains BIN CENTERS, not edges
      // So we need to calculate the top and bottom of each bin
      let binTop = price + (profileData.bin_size / 2);
      let binBottom = price - (profileData.bin_size / 2);
      
      // Skip bars completely outside the visible price range
      if (binBottom > maxPrice || binTop < minPrice) {
        return null;
      }
      
      // CLIP bin edges to visible price range (critical fix!)
      // If binTop is above maxPrice, clip it to maxPrice
      if (binTop > maxPrice) {
        binTop = maxPrice;
      }
      // If binBottom is below minPrice, clip it to minPrice
      if (binBottom < minPrice) {
        binBottom = minPrice;
      }
      
      // Calculate position in pixels relative to the effective height
      // Y position is from top of chart, so we need to calculate from maxPrice down
      const barTopPx = ((maxPrice - binTop) / priceRangeValue) * effectiveHeight; // pixels from top
      const barBottomPx = ((maxPrice - binBottom) / priceRangeValue) * effectiveHeight; // pixels from top
      const barHeightPx = barBottomPx - barTopPx; // height in pixels
      const barWidth = (volume / maxVolume) * 80; // % of max width (max 80% to make bars thinner)
      
      // Debug first few bars (only in DEBUG_MODE)
      if (DEBUG_MODE && index < 3) {
        console.log(`Bar ${index}:`, {
          price: price.toFixed(2),
          binTop: binTop.toFixed(2),
          binBottom: binBottom.toFixed(2),
          barTopPx: barTopPx.toFixed(2),
          barBottomPx: barBottomPx.toFixed(2),
          barHeightPx: barHeightPx.toFixed(2),
          clippedToRange: binTop !== (price + (profileData.bin_size / 2)) || binBottom !== (price - (profileData.bin_size / 2))
        });
      }
      
      // Final safety check - skip if bar has no height
      if (barHeightPx <= 0 || barTopPx < 0 || barBottomPx > effectiveHeight) {
        return null;
      }
      
      const isPOC = Math.abs(price - profileData.poc) < 0.01;
      const isInValueArea = price >= profileData.value_area.low && price <= profileData.value_area.high;
      const isHVN = profileData.hvn_levels.some(hvn => Math.abs(price - hvn) < 0.01);
      
      let className = 'vp-bar';
      if (isPOC) className += ' poc';
      else if (isHVN) className += ' hvn';
      else if (isInValueArea) className += ' value-area';
      
      return {
        price,
        yPositionPx: barTopPx,
        barHeightPx: barHeightPx,
        barWidth,
        className,
        volume
      };
    })
    .filter(bar => bar !== null); // Remove null bars

  return (
    <div 
      className="volume-profile-overlay" 
      style={{ 
        height: `${chartHeight}px`
      }}
    >
      {/* Bars Container */}
      <div 
        className="vp-bars-container" 
        style={{ 
          height: `${effectiveHeight}px`,
          top: `${topOffset}px`
        }}
      >
        {bars.map((bar, index) => (
          <div
            key={index}
            className={bar.className}
            style={{
              top: `${bar.yPositionPx}px`,
              height: `${bar.barHeightPx}px`,
              width: `${bar.barWidth}%`
            }}
            title={`${formatPrice(bar.price, { ticker_symbol: profileData && profileData.ticker ? profileData.ticker : null })} - ${bar.volume.toLocaleString()}`}
          />
        ))}
      </div>

      {/* Key Level Labels */}
      <div 
        className="vp-level-labels"
        style={{
          height: `${effectiveHeight}px`,
          top: `${topOffset}px`
        }}
      >
        <div 
          className="vp-label poc"
          style={{ top: `${((maxPrice - profileData.poc) / priceRangeValue) * effectiveHeight}px` }}
        >
          <span className="label-text">POC {formatPrice(profileData.poc, profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null)}</span>
        </div>
        <div 
          className="vp-label vah"
          style={{ top: `${((maxPrice - profileData.value_area.high) / priceRangeValue) * effectiveHeight}px` }}
        >
          <span className="label-text">VAH {formatPrice(profileData.value_area.high, profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null)}</span>
        </div>
        <div 
          className="vp-label val"
          style={{ top: `${((maxPrice - profileData.value_area.low) / priceRangeValue) * effectiveHeight}px` }}
        >
          <span className="label-text">VAL {formatPrice(profileData.value_area.low, profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null)}</span>
        </div>
      </div>
    </div>
  );
}

export default VolumeProfileOverlay;
