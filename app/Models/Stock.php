<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Stock extends Model
{
    protected $fillable = [
        'ticker',
        'trends',
        'name',
        'last_price_update',
        'last_image_update',
        'last_forecast_update',
    ];

    public function prices() {
        return $this->hasMany(StockPrice::class);
    }

    public function images() {
        return $this->hasMany(StockImage::class);
    }

    public function forecasts() {
        return $this->hasMany(StockForecast::class);
    }
}
