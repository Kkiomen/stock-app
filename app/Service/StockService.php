<?php

namespace App\Service;

use App\Core\Service\AbstractService;
use App\Models\Stock;
use App\Models\StockForecast;

class StockService extends AbstractService
{
    const MODEL = Stock::class;

    public function __construct(
        private StockPriceService $stockPriceService,
        private StockImageService $stockImageService,
        private StockForecastService $stockForecastService,
    ){}

    /**
     * Retrieves a stock by its ticker symbol, or creates a new stock if it does not exist.
     *
     * @param string $ticker The ticker symbol of the stock.
     * @return Stock The stock model instance.
     */
    public function getOrCreateByTicker(string $ticker): Stock
    {
        $stock = Stock::where('ticker', $ticker)->first();

        if (!$stock) {
            $stock = new Stock();
            $stock->ticker = $ticker;
            $stock->save();
        }

        return $stock;
    }

    public function savePrices(Stock $stock, array $data): Stock
    {
        $stockPrices = [];

        foreach ($data['stock_data'] as $priceData){
            $priceData['uuid'] = $data['uuid'];
            $priceData['stock_id'] = $stock->id;

            $stockPrice = $this->stockPriceService->savePrice($priceData);

            if($stockPrice !== null) {
                $stockPrices[] = $stockPrice;
            }
        }

        $stock->update([
            'last_price_update' => now()
        ]);

        return $stock;
    }

    public function saveImages(Stock $stock, array $data): Stock
    {
        $data['type'] = 'model';
        $data['stock_id'] = $stock->id;

        $data['base64'] = $data['base64'] ?? $data['image'] ?? null;
        $stockImage = $this->stockImageService->save(model: null, data: $data);

        $stock->update([
            'last_image_update' => now()
        ]);

        return $stockImage;
    }

    public function saveForecasts(Stock $stock, array $data): array
    {
        $stockForecasts = [];

        foreach ($data['forecast'] as $forecastData){

            $preparedData = [
                'stock_id' => $stock->id,
                'uuid' => $data['uuid'],
                'date' => $forecastData['index'],
                'close' => $forecastData['forecast_close'],
            ];

            $stockForeCast = $this->stockForecastService->save(data: $preparedData);

            if($stockForeCast !== null) {
                $stockForecasts[] = $stockForeCast;
            }
        }

        $stock->update([
            'last_forecast_update' => now()
        ]);

        return $stockForecasts;
    }
}
