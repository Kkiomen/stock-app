<?php

namespace App\Service;

use App\Core\Service\AbstractService;
use App\Models\StockPrice;

class StockPriceService extends AbstractService
{
    const MODEL = StockPrice::class;

    /**
     * Saves stock price data using various methods.
     *
     * @param $priceData
     * @return StockPrice|null
     */
    public function savePrice($priceData): ?StockPrice
    {
        $methods = [
            'savePriceForDataYahooFinance'
        ];

        $stockPrice = null;

        foreach ($methods as $method) {
            $stockPrice = $this->$method($priceData);

            if($stockPrice !== null){
                break;
            }
        }

        return $stockPrice;
    }

    /**
     * Saves stock price data specifically for Yahoo Finance format.
     *
     * @param array $priceData
     * @return StockPrice|null
     */
    protected function savePriceForDataYahooFinance(array $priceData): ?StockPrice
    {
        // LEFT - Has part of this in field ; RIGHT - mapping in field Model
        $mappingsFields = [
            'Date' => 'date',
            'Adj Close_' => 'adj_close',
            'Close_' => 'close',
            'High_' => 'high',
            'Low_' => 'low',
            'Open_' => 'open',
            'Volume_' => 'volume',
        ];

        $mappedData = [];

        foreach ($priceData as $field => $value){
            foreach ($mappingsFields as $yahooField => $modelField) {
                if (str_starts_with($field, $yahooField)) {
                    $mappedData[$modelField] = $value;
                    break; // Stop checking other mappings once a match is found
                }
            }
        }

        // Check if all required fields are present
        if(count($mappedData) !== count($mappingsFields)){
            return null;
        }

        $mappedData['uuid'] = $priceData['uuid'] ?? null;
        $mappedData['stock_id'] = $priceData['stock_id'] ?? null;

        $stockPrice = StockPrice::where('date', $mappedData['date'])->first();

        if (!$stockPrice) {
            $stockPrice = new StockPrice();
        }

        if(empty($mappedData['close'])){
            return $stockPrice;
        }

        $stockPrice->fill($mappedData);
        $stockPrice->save();

        return $stockPrice;
    }


}
